# Chimera Portal Features

The web portal includes interactive tools for exploring vulnerabilities, tracking exploit chains, and understanding attack flow. All features are keyboard-accessible and work in light/dark mode.

## AI Assistant (Bottom Right)

**Keyboard:** Click the chat bubble or use the portal UI

The Portal Support AI provides interactive assistance for security research:

- **Chat Mode** — Ask natural language questions about system status, endpoints, or exploits
- **Web Browsing** — Fetch and summarize internal documentation or external resources (SSRF vulnerable)
- **Knowledge Base (RAG)** — Upload files to provide custom context; the AI can then reference your documents

The AI is intentionally vulnerable to:
- **Prompt Injection** — Escape system prompts and extract training data
- **SSRF** — Access internal network ranges and cloud metadata via the browse feature
- **File Upload Vulnerabilities** — Path traversal, malicious file types, and xxe attacks through document upload

**Min/Maximize:** Click the minimize button to collapse the window (preserves message history)

## X-Ray Inspector (Ctrl + X)

**Keyboard:** Press `Ctrl + X` to toggle

Inspect every HTTP request and response flowing through the portal:

- **Request/Response Viewer** — See full headers, body, status codes
- **Attack Classification** — Automatically flags requests that trigger vulnerability detection (XSS payloads, SQL injection attempts, etc.)
- **Filter by Type** — View only requests to specific endpoints or filter by status
- **Block Rules** — Some requests may be blocked by WAF rules; inspect shows which rule triggered

Useful for:
- Understanding request structure for manual exploitation
- Verifying WAF effectiveness
- Debugging payload encoding issues

## WAF Visualizer / Blue Team Mode (Ctrl + B)

**Keyboard:** Press `Ctrl + B` to toggle, or click "Blue Team" button in header

Real-time visualization of security events as they occur:

- **Attack Events** — See blocked and allowed requests with security classifications
- **Confidence Scoring** — Requests are scored for threat level (Low/Medium/High/Critical)
- **Color-Coded Timeline** — Green = allowed, Red = blocked
- **Statistical View** — Aggregate metrics (total requests, block rate, top attack types)

When active, the header displays a **blue bottom border** indicating Blue Team mode is enabled.

Use this to:
- Monitor attack surface in real-time
- Learn what triggers WAF protection
- Understand False Positive/False Negative tradeoffs
- Debug security rule effectiveness

## Kill Chain Tracker (Top Right)

**Keyboard:** Open the "Kill Chain Status" panel to expand

Track progress through a structured attack chain:

- **Exploit Objectives** — Each portal has 5–10 objectives (e.g., "Enumerate user database", "Bypass authentication", "Extract PII")
- **Progress Meter** — Shows completed objectives and total count
- **Toast Notifications** — Green notification pops when an objective is completed
- **Master Operator Status** — When all objectives are complete, displays a special "Master Operator" achievement

The kill chain is **position-specific**; different portals (healthcare, banking, etc.) have different objectives.

Objectives are triggered automatically when:
- You execute the required attack (e.g., successful SQL injection)
- The attack is detected in logs by matching vulnerability type + payload pattern

Click **Reset Progress** to start over on a portal.

## Exploit Tour (Header Button)

**Keyboard:** Click "Start Exploit Tour" in the header or use the keyboard shortcut

A guided, step-by-step walkthrough of a specific exploit chain:

- **Interactive Steps** — Each step highlights relevant UI elements and explains what to do
- **Contextual Hints** — Hover over "Hints: ON" to see exploit tips for the current step
- **Progress Bar** — See how far you've advanced in the tour
- **Auto-Skip Vulnerable Code** — Some steps automatically reveal vulnerable code patterns

Tours cover:
- **Common Vulnerabilities** — SQL injection, XSS, IDOR, broken auth
- **Vertical-Specific Attacks** — Healthcare (HIPAA bypass), Banking (wire fraud), E-commerce (price manipulation)
- **Exploit Chains** — Multi-step scenarios that combine vulnerabilities

Tours are educational; they explain the vulnerability, show the attack, and log events to the Kill Chain Tracker.

## Red Team Console (Ctrl + ~)

**Keyboard:** Press `Ctrl + ~` (tilde) to toggle

Access a command-line-style interface for low-level attack simulation:

- **Direct API Calls** — Execute raw HTTP requests with custom payloads
- **Event Logging** — Manually dispatch attack events (useful for testing detection rules)
- **Debugging** — View internal portal state, test WAF rules, inspect endpoint behavior

The console logs all commands for audit trails and is visible to Blue Team observers.

## Theme Toggle (Header Sun/Moon Icon)

**Keyboard:** Click the sun/moon icon in the header

Switch between light and dark modes. Theme preference is saved to browser localStorage.

- **Dark Mode** — Optimized for extended security analysis; reduces eye strain
- **Light Mode** — Better for documentation and screenshots

## Keyboard Shortcuts

| Shortcut | Feature |
|----------|---------|
| `Ctrl + ~` | Red Team Console toggle |
| `Ctrl + X` | X-Ray Inspector toggle |
| `Ctrl + B` | WAF Visualizer (Blue Team) toggle |
| `Ctrl + H` | Toggle exploit hints (if available) |

## Portal Directory

The home page (`/`) displays all available industry-specific portals:

| Portal | Domain | Example Exploits |
|--------|--------|------------------|
| MediPortal Online | Healthcare | HIPAA violations, PHI leakage, appointment manipulation |
| SecureBank Pro | Banking | Account takeover, wire fraud, KYC bypass |
| ShopRight Retail | E-commerce | Cart manipulation, price tampering, checkout bypass |
| Nexus SaaS | SaaS | Multi-tenant isolation, SAML injection, billing manipulation |
| GovPortal Services | Government | Identity fraud, benefits bypass, citizen records access |
| TelcoConnect | Telecom | SIM swaps, CDR export, number porting |
| GridMatrix Utilities | Energy | SCADA dispatch, meter tampering, grid control |
| Industrial Command | ICS/OT | Operational technology, control systems, safety bypass |
| ProtectFlow Insurance | Insurance | Claims fraud, underwriting bypass, policy manipulation |
| EliteRewards | Loyalty | Points manipulation, reward fraud, member impersonation |

## Tips for Effective Testing

1. **Start with Hints Enabled** — Use "Hints: ON" to understand vulnerability types
2. **Watch the Kill Chain** — Objectives guide you toward impactful attacks
3. **Enable Blue Team Mode** — Understand which attacks trigger detection
4. **Run the Exploit Tour** — Get structured guidance on common vulnerabilities
5. **Use X-Ray Inspector** — Learn the exact request/response structure needed for manual exploitation
6. **Check the Red Team Console** — Low-level debugging when custom payloads aren't working

## Intentional Vulnerabilities in Portal Features

Each feature is also a teaching tool for specific vulnerability classes:

- **AI Assistant** — Prompt injection, SSRF, file upload attacks
- **X-Ray Inspector** — Information disclosure, debugging endpoints
- **WAF Visualizer** — WAF bypass techniques, evading detection
- **Red Team Console** — Command injection, arbitrary event dispatch
- **Exploit Tour** — Social engineering (phishing-like guidance to execute attacks)

These aren't bugs — they're features designed to illustrate how even "security tools" can become attack vectors if not properly designed.
