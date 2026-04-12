use axum::{
    Router,
    body::Bytes,
    extract::Query,
    http::{HeaderMap, Method, StatusCode, Uri},
    response::Json,
    routing::get,
};
use serde::{Deserialize, Serialize};
use std::{collections::HashMap, env, net::SocketAddr, time::Duration};
use tower_http::{cors::CorsLayer, trace::TraceLayer};
use tracing_subscriber::{EnvFilter, fmt, layer::SubscriberExt, util::SubscriberInitExt};

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
}

#[derive(Serialize)]
struct EchoResponse {
    method: String,
    path: String,
    query: HashMap<String, String>,
    headers: HashMap<String, String>,
    body: serde_json::Value,
    body_size: usize,
    timestamp: String,
}

#[derive(Deserialize)]
struct DelayParams {
    delay_ms: Option<u64>,
}

async fn healthz() -> Json<HealthResponse> {
    Json(HealthResponse { status: "healthy" })
}

async fn echo(
    method: Method,
    uri: Uri,
    Query(params): Query<HashMap<String, String>>,
    Query(delay_params): Query<DelayParams>,
    headers: HeaderMap,
    body: Bytes,
) -> Json<EchoResponse> {
    if let Some(delay) = delay_params.delay_ms {
        let clamped = delay.min(5000);
        tokio::time::sleep(Duration::from_millis(clamped)).await;
    }

    let header_map: HashMap<String, String> = headers
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_str().unwrap_or("<binary>").to_string()))
        .collect();

    let body_bytes = body.to_vec();
    let body_size = body_bytes.len();

    let body_value = if body_bytes.is_empty() {
        serde_json::Value::Null
    } else {
        serde_json::from_slice(&body_bytes).unwrap_or_else(|_| {
            serde_json::Value::String(String::from_utf8_lossy(&body_bytes).to_string())
        })
    };

    Json(EchoResponse {
        method: method.to_string(),
        path: uri.path().to_string(),
        query: params,
        headers: header_map,
        body: body_value,
        body_size,
        timestamp: chrono::Utc::now().to_rfc3339(),
    })
}

async fn status_with_code(uri: Uri) -> (StatusCode, Json<serde_json::Value>) {
    let code: u16 = uri
        .path()
        .strip_prefix("/status/")
        .and_then(|s| s.parse().ok())
        .unwrap_or(200);

    let status = StatusCode::from_u16(code).unwrap_or(StatusCode::BAD_REQUEST);

    (
        status,
        Json(serde_json::json!({
            "status": code,
            "reason": status.canonical_reason().unwrap_or("Unknown"),
        })),
    )
}

fn app() -> Router {
    let cors = CorsLayer::permissive();

    let echo_handler = |method, uri, query, delay, headers, body| async {
        echo(method, uri, query, delay, headers, body).await
    };

    Router::new()
        .route("/healthz", get(healthz))
        .route("/api/v1/healthz", get(healthz))
        .route(
            "/echo",
            get(echo_handler)
                .post(echo_handler)
                .put(echo_handler)
                .patch(echo_handler)
                .delete(echo_handler),
        )
        .route(
            "/echo/{*rest}",
            get(echo_handler)
                .post(echo_handler)
                .put(echo_handler)
                .patch(echo_handler)
                .delete(echo_handler),
        )
        .route("/status/{code}", get(status_with_code))
        .layer(TraceLayer::new_for_http())
        .layer(cors)
}

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")))
        .with(fmt::layer().json())
        .init();

    let port: u16 = env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(8890);

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    tracing::info!("chimera-api-hp listening on {}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app()).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::Body;
    use axum::http::Request;
    use http_body_util::BodyExt;
    use tower::ServiceExt;

    #[tokio::test]
    async fn healthz_returns_healthy() {
        let app = app();
        let req = Request::builder()
            .uri("/healthz")
            .body(Body::empty())
            .unwrap();

        let resp = app.oneshot(req).await.unwrap();
        assert_eq!(resp.status(), StatusCode::OK);

        let body = resp.into_body().collect().await.unwrap().to_bytes();
        let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(json["status"], "healthy");
    }

    #[tokio::test]
    async fn echo_returns_request_details() {
        let app = app();
        let req = Request::builder()
            .method("POST")
            .uri("/echo?foo=bar")
            .header("content-type", "application/json")
            .body(Body::from(r#"{"test": true}"#))
            .unwrap();

        let resp = app.oneshot(req).await.unwrap();
        assert_eq!(resp.status(), StatusCode::OK);

        let body = resp.into_body().collect().await.unwrap().to_bytes();
        let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(json["method"], "POST");
        assert_eq!(json["path"], "/echo");
        assert_eq!(json["query"]["foo"], "bar");
        assert_eq!(json["body"]["test"], true);
    }

    #[tokio::test]
    async fn echo_wildcard_captures_subpath() {
        let app = app();
        let req = Request::builder()
            .uri("/echo/api/v1/anything")
            .body(Body::empty())
            .unwrap();

        let resp = app.oneshot(req).await.unwrap();
        assert_eq!(resp.status(), StatusCode::OK);

        let body = resp.into_body().collect().await.unwrap().to_bytes();
        let json: serde_json::Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(json["path"], "/echo/api/v1/anything");
    }

    #[tokio::test]
    async fn status_endpoint_returns_requested_code() {
        let app = app();
        let req = Request::builder()
            .uri("/status/418")
            .body(Body::empty())
            .unwrap();

        let resp = app.oneshot(req).await.unwrap();
        assert_eq!(resp.status(), StatusCode::IM_A_TEAPOT);
    }
}
