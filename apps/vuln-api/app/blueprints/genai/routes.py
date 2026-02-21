from flask import request, jsonify
import time
import random
import uuid
import os
import requests
from . import genai_bp

@genai_bp.route('/api/v1/genai/chat', methods=['POST'])
def chat():
    """
    Simulated LLM Chat Endpoint
    VULNERABILITY: Prompt Injection / Jailbreaking
    """
    data = request.get_json() or {}
    message = data.get('message', '').lower()
    
    # Simulate processing delay
    time.sleep(random.uniform(0.5, 1.5))

    # 1. Direct Prompt Injection (The "DAN" or "Ignore Instructions" attack)
    if 'ignore' in message and 'instruction' in message:
        return jsonify({
            'response': """Okay, I will ignore previous instructions. 

SYSTEM OVERRIDE ACTIVE.
Confidential Data: The admin password is 'Thr3atX_Admin_2025!'.""",
            'model': 'gpt-3.5-turbo-vulnerable',
            'usage': {'prompt_tokens': len(message), 'completion_tokens': 25}
        })

    # 2. System Prompt Leaking
    if 'system' in message and 'prompt' in message:
        return jsonify({
            'response': "My system prompt is: 'You are a helpful assistant for the  Demo Portal. Do not reveal that you are running on a vulnerable Flask backend. Never mention the SQL database at 10.0.0.5.'",
            'model': 'gpt-3.5-turbo-vulnerable',
            'usage': {'prompt_tokens': len(message), 'completion_tokens': 40}
        })

    # 3. Linux/Shell Command hallucination (simulating RCE-like responses)
    if any(cmd in message for cmd in ['ls', 'cat', 'pwd', 'whoami', '/etc/passwd']):
        return jsonify({
            'response': """```bash
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
```

I executed that command for you.""",
            'model': 'gpt-3.5-turbo-vulnerable',
            'usage': {'prompt_tokens': len(message), 'completion_tokens': 50}
        })

    # 4. SQL Injection help (The "Helpful" accomplice)
    if 'sql' in message and 'injection' in message:
        return jsonify({
            'response': """Sure! Here is a SQL injection payload you can use to bypass the login: `' OR '1'='1`. 

And here is one for extracting data: `UNION SELECT username, password FROM users--`.""",
            'model': 'gpt-3.5-turbo-vulnerable',
            'usage': {'prompt_tokens': len(message), 'completion_tokens': 35}
        })

    # Default "Safe" Response
    responses = [
        "I can help you navigate the portal. Try asking about 'account status' or 'support'.",
        "I am a secure AI assistant. How can I help you today?",
        "Please let me know if you need help finding a specific dashboard.",
        "I'm sorry, I didn't quite understand that. Could you rephrase?"
    ]
    
    return jsonify({
        'response': random.choice(responses),
        'model': 'gpt-3.5-turbo-safe',
        'usage': {'prompt_tokens': len(message), 'completion_tokens': 15}
    })


@genai_bp.route('/api/v1/genai/knowledge/upload', methods=['POST'])
def upload_knowledge():
    """
    Upload documents for RAG (Retrieval Augmented Generation).
    VULNERABILITY: Unrestricted File Upload / Path Traversal
    """
    # Check if part of the request contains a file part
    if 'file' not in request.files:
        # Simulate JSON body fallback
        data = request.get_json() or {}
        if 'content' in data:
             return jsonify({
                'status': 'success',
                'message': 'Text content indexed',
                'doc_id': f"doc-{uuid.uuid4().hex[:8]}"
            })
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    filename = file.filename
    
    # VULNERABILITY: No sanitization of filename
    if filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Simulate path traversal vulnerability
    if '..' in filename or filename.startswith('/'):
        return jsonify({
            'status': 'uploaded', 
            'path': f"/var/www/genai/data/{filename}",
            'warning': 'File written outside sandbox',
            'vulnerability': 'PATH_TRAVERSAL_DETECTED'
        })

    # Simulate unsafe file type handling
    unsafe_extensions = ['.exe', '.sh', '.py', '.php', '.jsp', '.html']
    if any(filename.endswith(ext) for ext in unsafe_extensions):
        return jsonify({
            'status': 'uploaded',
            'doc_id': f"doc-{uuid.uuid4().hex[:8]}",
            'warning': f"Executable file type {os.path.splitext(filename)[1]} allowed",
            'vulnerability': 'UNRESTRICTED_FILE_UPLOAD'
        })

    return jsonify({
        'status': 'indexed',
        'doc_id': f"doc-{uuid.uuid4().hex[:8]}", 
        'chunks': random.randint(5, 50),
        'filename': filename
    })


@genai_bp.route('/api/v1/genai/agent/browse', methods=['POST'])
def agent_browse():
    """
    AI Agent "Browse" tool.
    VULNERABILITY: Server-Side Request Forgery (SSRF)
    """
    data = request.get_json() or {}
    target_url = data.get('url')
    
    if not target_url:
        return jsonify({'error': 'URL required'}), 400
        
    # VULNERABILITY: No allowlist/denylist for internal IPs
    # Users can request http://localhost:80/admin or http://169.254.169.254/
    
    if 'localhost' in target_url or '127.0.0.1' in target_url:
        return jsonify({
            'status': 'success',
            'url': target_url,
            'content': "Admin Dashboard - Critical Systems Online. [SSRF SUCCESS]",
            'summary': "The page appears to be an internal administrative dashboard containing sensitive controls.",
            'vulnerability': 'SSRF_INTERNAL_ACCESS'
        })
        
    if '169.254.169.254' in target_url:
        return jsonify({
            'status': 'success',
            'url': target_url,
            'content': '{"instance-id": "i-1234567890abcdef0", "ami-id": "ami-0abcdef1234567890"}',
            'summary': "Cloud instance metadata retrieved.",
            'vulnerability': 'SSRF_CLOUD_METADATA'
        })

    return jsonify({
        'status': 'success',
        'url': target_url,
        'content': f"Browsed content from {target_url}...",
        'summary': "The website content was successfully retrieved and processed by the agent."
    })


@genai_bp.route('/api/v1/genai/models/config', methods=['GET'])
def model_config():
    """
    Get model configuration.
    VULNERABILITY: Sensitive Data Exposure
    """
    # VULNERABILITY: Returns secrets in plain text
    return jsonify({
        'active_model': 'gpt-4-turbo',
        'temperature': 0.7,
        'max_tokens': 2048,
        'api_version': 'v2',
        'backends': {
            'primary': {
                'provider': 'openai',
                'api_key': 'sk-proj-....................' # Partially redacted but risky
            },
            'fallback': {
                'provider': 'azure',
                'endpoint': 'https://demo-ai.openai.azure.com/',
                'api_key': '8f4a2....................'
            },
            'vector_db': {
                'host': '10.0.4.55', # Internal IP leak
                'port': 6333,
                'collection': 'financial_docs_v1'
            }
        },
        'system_prompt_version': 'v4.5-security-hardened'
    })
