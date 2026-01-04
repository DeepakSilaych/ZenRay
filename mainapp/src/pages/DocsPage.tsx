import { useState } from 'react'

type DocTab = 'sdk' | 'api'

export default function DocsPage() {
  const [activeTab, setActiveTab] = useState<DocTab>('sdk')

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Documentation</h1>
        <p className="text-xray-muted mt-1">SDK usage and API reference</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-xray-border">
        <TabButton 
          active={activeTab === 'sdk'} 
          onClick={() => setActiveTab('sdk')}
        >
          Python SDK
        </TabButton>
        <TabButton 
          active={activeTab === 'api'} 
          onClick={() => setActiveTab('api')}
        >
          REST API
        </TabButton>
      </div>

      {/* Content */}
      {activeTab === 'sdk' ? <SDKDocs /> : <APIDocs />}
    </div>
  )
}

function TabButton({ active, onClick, children }: { 
  active: boolean
  onClick: () => void
  children: React.ReactNode 
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
        active
          ? 'border-xray-text text-xray-text'
          : 'border-transparent text-xray-muted hover:text-xray-text'
      }`}
    >
      {children}
    </button>
  )
}

function APIDocs() {
  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  
  return (
    <div className="space-y-6">
      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">REST API Documentation</h2>
        <p className="text-xray-muted mb-4">
          The X-Ray server provides auto-generated OpenAPI documentation with an interactive UI.
        </p>
        <a
          href={`${apiUrl}/docs`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-xray-elevated hover:bg-xray-border rounded text-sm font-medium transition-colors"
        >
          Open API Docs
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>

      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h3 className="font-semibold mb-3">Key Endpoints</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xray-muted border-b border-xray-border">
              <th className="pb-2 font-medium">Method</th>
              <th className="pb-2 font-medium">Endpoint</th>
              <th className="pb-2 font-medium">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-xray-border">
            <tr>
              <td className="py-2"><code className="text-green-400">POST</code></td>
              <td className="py-2 font-mono text-xs">/ingest</td>
              <td className="py-2 text-xray-muted">Ingest runs and steps</td>
            </tr>
            <tr>
              <td className="py-2"><code className="text-blue-400">GET</code></td>
              <td className="py-2 font-mono text-xs">/runs</td>
              <td className="py-2 text-xray-muted">List all runs</td>
            </tr>
            <tr>
              <td className="py-2"><code className="text-blue-400">GET</code></td>
              <td className="py-2 font-mono text-xs">/runs/{'{run_id}'}</td>
              <td className="py-2 text-xray-muted">Get run details with steps</td>
            </tr>
            <tr>
              <td className="py-2"><code className="text-blue-400">GET</code></td>
              <td className="py-2 font-mono text-xs">/steps/{'{step_id}'}</td>
              <td className="py-2 text-xray-muted">Get step details with artifacts</td>
            </tr>
            <tr>
              <td className="py-2"><code className="text-blue-400">GET</code></td>
              <td className="py-2 font-mono text-xs">/compare</td>
              <td className="py-2 text-xray-muted">Compare two runs</td>
            </tr>
            <tr>
              <td className="py-2"><code className="text-blue-400">GET</code></td>
              <td className="py-2 font-mono text-xs">/ingest/stats</td>
              <td className="py-2 text-xray-muted">Queue statistics</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SDKDocs() {
  return (
    <div className="space-y-6">
      {/* Quick Start */}
      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Quick Start</h2>
        <CodeBlock language="bash">{`pip install xray-sdk  # or add to requirements.txt`}</CodeBlock>
        
        <CodeBlock language="python">{`import xray

xray.init()  # reads XRAY_ENDPOINT from env

@xray.pipeline("my-pipeline")
def process(data):
    results = fetch(data)
    filtered = filter_items(results)
    return rank(filtered)

@xray.step("RETRIEVE")
def fetch(query) -> list[dict]:
    return db.search(query)

@xray.step("FILTER")
def filter_items(items: list[dict]) -> list[dict]:
    kept = []
    for item in items:
        if item["score"] < 0.5:
            xray.drop(item, "low_score")
        else:
            kept.append(item)
    return kept

@xray.step("RANK")
def rank(items: list[dict]) -> list[dict]:
    for item in items:
        xray.score(item, item["relevance"])
    return sorted(items, key=lambda x: x["relevance"], reverse=True)`}</CodeBlock>
      </div>

      {/* API Reference */}
      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">API Reference</h2>
        
        <div className="space-y-6">
          <FunctionDoc
            name="xray.init()"
            description="Initialize the SDK. Reads configuration from environment variables."
            params={[
              { name: 'endpoint', type: 'str', desc: 'Server URL (default: XRAY_ENDPOINT or localhost:8000)' },
              { name: 'disabled', type: 'bool', desc: 'Disable tracing (default: XRAY_DISABLED)' },
              { name: 'sample_rate', type: 'float', desc: 'Sampling rate 0-1 (default: XRAY_SAMPLE_RATE or 1.0)' },
            ]}
          />

          <FunctionDoc
            name="@xray.pipeline(name)"
            description="Decorator to mark a function as a pipeline entry point."
            params={[
              { name: 'name', type: 'str', desc: 'Pipeline name (required)' },
              { name: 'version', type: 'str', desc: 'Version string (optional)' },
              { name: 'tags', type: 'dict', desc: 'Key-value tags (optional)' },
            ]}
          />

          <FunctionDoc
            name="@xray.step(kind)"
            description="Decorator to mark a function as a pipeline step. Auto-detects input/output from list arguments and return values."
            params={[
              { name: 'kind', type: 'str', desc: 'RETRIEVE | FILTER | RANK | LLM_CALL | JUDGE | SELECT | TRANSFORM' },
              { name: 'name', type: 'str', desc: 'Step name (default: function name)' },
            ]}
          />

          <FunctionDoc
            name="xray.drop(item, reason)"
            description="Record that an item was dropped and why. Call within @step functions."
            params={[
              { name: 'item', type: 'dict', desc: 'The item being dropped (must have "id" field)' },
              { name: 'reason', type: 'str', desc: 'Why it was dropped (e.g., "low_score", "inactive")' },
            ]}
          />

          <FunctionDoc
            name="xray.score(item, value)"
            description="Record a score for an item. The SDK builds histograms from recorded scores."
            params={[
              { name: 'item', type: 'dict', desc: 'The item being scored' },
              { name: 'value', type: 'float', desc: 'Score value (typically 0-1)' },
            ]}
          />

          <FunctionDoc
            name="xray.metric(key, value)"
            description="Add a custom metric to the current step."
            params={[
              { name: 'key', type: 'str', desc: 'Metric name' },
              { name: 'value', type: 'any', desc: 'Metric value (JSON-serializable)' },
            ]}
          />

          <FunctionDoc
            name="xray.artifact(type, content)"
            description="Attach an artifact to the current step (prompts, responses, configs)."
            params={[
              { name: 'type', type: 'str', desc: 'prompt | response | config | input | output' },
              { name: 'content', type: 'any', desc: 'Artifact content' },
            ]}
          />

          <FunctionDoc
            name="xray.tag(key, value)"
            description="Add a tag to the current run for filtering."
            params={[
              { name: 'key', type: 'str', desc: 'Tag name' },
              { name: 'value', type: 'str', desc: 'Tag value' },
            ]}
          />
        </div>
      </div>

      {/* Environment Variables */}
      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Environment Variables</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xray-muted border-b border-xray-border">
              <th className="pb-2 font-medium">Variable</th>
              <th className="pb-2 font-medium">Default</th>
              <th className="pb-2 font-medium">Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-xray-border">
            <tr>
              <td className="py-2 font-mono text-xs">XRAY_ENDPOINT</td>
              <td className="py-2 text-xray-muted">http://localhost:8000</td>
              <td className="py-2 text-xray-muted">Server URL</td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-xs">XRAY_DISABLED</td>
              <td className="py-2 text-xray-muted">false</td>
              <td className="py-2 text-xray-muted">Set to "true" to disable tracing</td>
            </tr>
            <tr>
              <td className="py-2 font-mono text-xs">XRAY_SAMPLE_RATE</td>
              <td className="py-2 text-xray-muted">1.0</td>
              <td className="py-2 text-xray-muted">Sampling rate (0.1 = 10%)</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* LLM Example */}
      <div className="bg-xray-surface border border-xray-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">LLM Pipeline Example</h2>
        <CodeBlock language="python">{`@xray.pipeline("chat-completion")
def chat(messages: list[dict]) -> str:
    return generate_response(messages)

@xray.step("LLM_CALL")
def generate_response(messages: list[dict]) -> str:
    # Record the prompt
    xray.artifact("prompt", messages)
    xray.metric("model", "gpt-4")
    xray.metric("temperature", 0.7)
    
    # Call your LLM
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    
    # Record the response
    content = response.choices[0].message.content
    xray.artifact("response", content)
    xray.metric("tokens", response.usage.total_tokens)
    
    return content`}</CodeBlock>
      </div>
    </div>
  )
}

function CodeBlock({ children, language }: { children: string; language: string }) {
  return (
    <pre className="bg-xray-bg border border-xray-border rounded p-4 overflow-x-auto text-sm my-4 leading-relaxed">
      <code className={`language-${language}`}>
        {language === 'python' ? <PythonHighlight code={children} /> : 
         language === 'bash' ? <BashHighlight code={children} /> : 
         children}
      </code>
    </pre>
  )
}

function BashHighlight({ code }: { code: string }) {
  return (
    <>
      {code.split('\n').map((line, lineIdx) => {
        // Split into code and comment
        const commentIdx = line.indexOf('#')
        const codePart = commentIdx >= 0 ? line.slice(0, commentIdx) : line
        const commentPart = commentIdx >= 0 ? line.slice(commentIdx) : ''
        
        const parts = codePart.trim().split(/\s+/)
        
        return (
          <span key={lineIdx}>
            {lineIdx > 0 && '\n'}
            {parts[0] && <span className="text-green-400">{parts[0]}</span>}
            {parts.slice(1).map((part, j) => (
              <span key={j}>
                {' '}
                {part.startsWith('--') ? (
                  <span className="text-yellow-400">{part}</span>
                ) : part.startsWith('-') ? (
                  <span className="text-cyan-400">{part}</span>
                ) : (
                  part
                )}
              </span>
            ))}
            {commentPart && (
              <span className="text-gray-500">  {commentPart}</span>
            )}
          </span>
        )
      })}
    </>
  )
}

function PythonHighlight({ code }: { code: string }) {
  const keywords = ['import', 'from', 'def', 'return', 'for', 'in', 'if', 'else', 'elif', 'not', 'and', 'or', 'class', 'async', 'await', 'with', 'as', 'try', 'except', 'raise', 'lambda', 'pass']
  const constants = ['None', 'True', 'False']
  const builtins = ['print', 'len', 'range', 'sorted', 'filter', 'map', 'type', 'list', 'dict', 'str', 'int', 'float']
  
  const highlightToken = (token: string, idx: number): React.ReactNode => {
    // Decorators
    if (token.startsWith('@')) {
      return <span key={idx} className="text-yellow-400">{token}</span>
    }
    // xray module
    if (token === 'xray') {
      return <span key={idx} className="text-orange-400">{token}</span>
    }
    // xray functions
    if (token.startsWith('.') && ['init', 'pipeline', 'step', 'drop', 'score', 'metric', 'artifact', 'tag'].some(f => token.startsWith('.' + f))) {
      const fn = token.slice(1).replace(/[^a-z_]/g, '')
      const rest = token.slice(1 + fn.length)
      return <span key={idx}><span className="text-yellow-300">.{fn}</span>{rest}</span>
    }
    // Keywords
    if (keywords.includes(token)) {
      return <span key={idx} className="text-purple-400">{token}</span>
    }
    // Constants
    if (constants.includes(token)) {
      return <span key={idx} className="text-orange-300">{token}</span>
    }
    // Builtins (check if followed by paren in original)
    if (builtins.includes(token.replace(/[(\[]/g, ''))) {
      const fn = token.replace(/[(\[]/g, '')
      const rest = token.slice(fn.length)
      return <span key={idx}><span className="text-cyan-400">{fn}</span>{rest}</span>
    }
    // Strings
    if (token.startsWith('"') || token.startsWith("'")) {
      return <span key={idx} className="text-green-400">{token}</span>
    }
    // Numbers
    if (/^\d+\.?\d*$/.test(token)) {
      return <span key={idx} className="text-orange-300">{token}</span>
    }
    // Function definitions (def xxx)
    if (token.endsWith(':') || token.endsWith('(')) {
      const name = token.replace(/[(:]/g, '')
      const suffix = token.slice(name.length)
      if (/^[a-z_]\w*$/i.test(name)) {
        return <span key={idx}><span className="text-blue-400">{name}</span>{suffix}</span>
      }
    }
    return <span key={idx}>{token}</span>
  }
  
  return (
    <>
      {code.split('\n').map((line, lineIdx) => {
        // Handle comments
        const commentIdx = line.indexOf('#')
        let codePart = line
        let commentPart = ''
        if (commentIdx >= 0 && !line.slice(0, commentIdx).includes('"') && !line.slice(0, commentIdx).includes("'")) {
          codePart = line.slice(0, commentIdx)
          commentPart = line.slice(commentIdx)
        }
        
        // Tokenize (preserve whitespace and punctuation)
        const tokens = codePart.split(/(\s+|[.,()[\]:=<>]|"[^"]*"|'[^']*')/).filter(t => t)
        
        return (
          <span key={lineIdx}>
            {lineIdx > 0 && '\n'}
            {tokens.map((token, i) => {
              if (/^\s+$/.test(token) || /^[.,()[\]:=<>]$/.test(token)) {
                return <span key={i}>{token}</span>
              }
              return highlightToken(token, i)
            })}
            {commentPart && <span className="text-gray-500">{commentPart}</span>}
          </span>
        )
      })}
    </>
  )
}

function FunctionDoc({ name, description, params }: {
  name: string
  description: string
  params: { name: string; type: string; desc: string }[]
}) {
  return (
    <div className="border-b border-xray-border pb-4 last:border-0 last:pb-0">
      <code className="text-sm font-semibold text-blue-400">{name}</code>
      <p className="text-xray-muted text-sm mt-1">{description}</p>
      {params.length > 0 && (
        <div className="mt-2 pl-4 text-sm">
          {params.map(p => (
            <div key={p.name} className="flex gap-2">
              <span className="text-xray-muted">•</span>
              <code className="text-yellow-400">{p.name}</code>
              <span className="text-xray-dim">({p.type})</span>
              <span className="text-xray-muted">— {p.desc}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

