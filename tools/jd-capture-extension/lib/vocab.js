/* Vocabulary the JD scorer recognises. Used for both the JD text and the skills rows of the master resume,
 * so the same term resolves the same way on both sides.
 *
 * Entry: { t: canonical term, a: aliases (case-insensitive), cs: aliases matched case-sensitively,
 *          rx: custom regex sources, kind: 'skill' | 'concept' | 'domain', by: for concepts, skills that satisfy it }
 * A concept is satisfied by the best credit among its `by` skills. A domain is satisfied when the profile lists it.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.JDVocab = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  const S = (t, a, extra) => Object.assign({ t, a: a || [], kind: 'skill' }, extra || {});
  return [
    // Languages
    S('TypeScript', ['TypeScript', 'Typescript']),
    S('JavaScript', ['JavaScript', 'Javascript', 'ECMAScript'], { cs: ['JS'] }),
    S('Python', ['Python']),
    S('Java', [], { cs: ['Java'] }),
    S('Go', ['Golang'], { rx: ['(?<![A-Za-z0-9])Go(?=\\s*[,/)])', '\\b(?:in|with|using|and|or) Go\\b(?!-)'] }),
    S('Ruby', ['Ruby']),
    S('Rails', ['Ruby on Rails'], { cs: ['Rails', 'RoR'] }),
    S('Rust', [], { cs: ['Rust'] }),
    S('C#', [], { rx: ['(?<![A-Za-z0-9])C#'] }),
    S('.NET', [], { rx: ['(?<![A-Za-z0-9])\\.NET\\b'] }),
    S('Kotlin', ['Kotlin']), S('Swift', [], { cs: ['Swift'] }), S('PHP', [], { cs: ['PHP'] }), S('Scala', ['Scala']),
    // Frontend
    S('React', ['React', 'ReactJS', 'React.js']),
    S('Next.js', ['Next.js', 'NextJS']),
    S('React Native', ['React Native']),
    S('Vue', ['Vue', 'Vue.js']), S('Angular', ['Angular']), S('Svelte', ['Svelte']), S('Redux', ['Redux']),
    S('Vite', [], { cs: ['Vite'] }), S('Webpack', ['Webpack']),
    S('Tailwind CSS', ['Tailwind CSS', 'Tailwind']),
    S('HTML', [], { cs: ['HTML', 'HTML5'] }), S('CSS', [], { cs: ['CSS', 'CSS3'] }),
    S('TipTap', ['TipTap']), S('Figma', ['Figma']),
    S('Storybook', ['Storybook']),
    // Testing
    S('Jest', [], { cs: ['Jest'] }), S('Mocha', [], { cs: ['Mocha'] }), S('Chai', [], { cs: ['Chai'] }),
    S('React Testing Library', ['React Testing Library', 'Testing Library'], { cs: ['RTL'] }),
    S('Cypress', [], { cs: ['Cypress'] }), S('Playwright', ['Playwright']), S('Selenium', ['Selenium']), S('Vitest', ['Vitest']),
    // Backend
    S('Node.js', ['Node.js', 'NodeJS', 'Node js'], { cs: ['Node'] }),
    S('Express', ['Express.js', 'ExpressJS'], { cs: ['Express'] }),
    S('NestJS', ['NestJS', 'Nest.js']),
    S('Fastify', ['Fastify']), S('Django', ['Django']), S('Flask', ['Flask']), S('FastAPI', ['FastAPI']),
    S('Spring Boot', ['Spring Boot', 'Spring Framework'], { cs: ['Spring'] }),
    S('GraphQL', ['GraphQL']), S('gRPC', ['gRPC']),
    S('REST', ['RESTful', 'REST APIs', 'REST API'], { cs: ['REST'] }),
    S('WebSocket', ['WebSocket', 'WebSockets', 'web sockets']),
    S('SSE', ['server-sent events'], { cs: ['SSE'] }),
    S('Kafka', ['Kafka']), S('RabbitMQ', ['RabbitMQ']), S('SQS', [], { cs: ['SQS'] }), S('BullMQ', ['BullMQ']), S('Redis', ['Redis']),
    S('microservices', ['microservices', 'microservice', 'micro-services', 'microservices architecture']),
    S('event-driven', ['event-driven', 'event driven', 'event-driven design', 'event-driven architecture']),
    S('serverless', ['serverless']),
    S('Temporal', [], { cs: ['Temporal'] }),
    // Data
    S('PostgreSQL', ['PostgreSQL', 'Postgres', 'Postgre']),
    S('MySQL', ['MySQL']), S('MongoDB', ['MongoDB', 'Mongo']), S('DynamoDB', ['DynamoDB']),
    S('Elasticsearch', ['Elasticsearch', 'OpenSearch']), S('Snowflake', ['Snowflake']), S('Redshift', ['Redshift']),
    S('ClickHouse', ['ClickHouse']), S('Turso', ['Turso']),
    S('SQL', [], { cs: ['SQL'] }), S('NoSQL', ['NoSQL']), S('OLAP', [], { cs: ['OLAP'] }),
    // Infra and delivery
    S('AWS', ['AWS', 'Amazon Web Services']), S('S3', [], { cs: ['S3'] }), S('CloudFront', ['CloudFront']), S('EC2', [], { cs: ['EC2'] }),
    S('GCP', ['Google Cloud', 'GCP']), S('Azure', ['Azure']),
    S('Cloudflare', ['Cloudflare Workers', 'Cloudflare']),
    S('Docker', ['Docker', 'containerization', 'containerisation']),
    S('Kubernetes', ['Kubernetes'], { cs: ['K8s'] }),
    S('Terraform', ['Terraform']), S('Helm', [], { cs: ['Helm'] }), S('Karpenter', ['Karpenter']), S('GitOps', ['GitOps']),
    S('GitHub Actions', ['GitHub Actions']), S('GitLab CI', ['GitLab CI']), S('Jenkins', ['Jenkins']), S('ArgoCD', ['ArgoCD', 'Argo CD']),
    S('Nx', [], { cs: ['Nx'] }), S('Turborepo', ['Turborepo']), S('monorepo', ['monorepo', 'monorepos']),
    S('Istio', ['Istio']),
    S('Prometheus', ['Prometheus']), S('Grafana', ['Grafana']), S('Datadog', ['Datadog']), S('OpenTelemetry', ['OpenTelemetry']),
    S('New Relic', ['New Relic']), S('Sentry', ['Sentry']), S('ELK', [], { cs: ['ELK'] }),
    // AI
    S('LLM', ['LLM', 'LLMs', 'large language model', 'large language models']),
    S('Claude API', ['Claude API', 'Claude Code', 'Anthropic API', 'Claude']),
    S('OpenAI API', ['OpenAI API', 'OpenAI']),
    S('Langfuse', ['Langfuse']),
    S('RAG', [], { cs: ['RAG'] }), S('MCP', [], { cs: ['MCP'] }),
    S('agents', ['AI agents', 'agentic', 'multi-agent', 'agent frameworks']),
    S('prompt engineering', ['prompt engineering']),
    S('PyTorch', ['PyTorch']), S('TensorFlow', ['TensorFlow']),
    // Data and ML
    S('Pandas', ['Pandas']), S('NumPy', ['NumPy']), S('SciPy', ['SciPy']), S('scikit-learn', ['scikit-learn', 'sklearn']), S('Jupyter', ['Jupyter']),
    S('Spark', ['Apache Spark', 'PySpark'], { cs: ['Spark'] }), S('Hadoop', ['Hadoop']), S('Airflow', ['Airflow']), S('dbt', [], { cs: ['dbt'] }),
    S('Databricks', ['Databricks']), S('Flink', ['Flink']), S('MLflow', ['MLflow']), S('Tableau', ['Tableau']), S('Power BI', ['Power BI']),
    S('ETL', [], { cs: ['ETL', 'ELT'] }), S('LangChain', ['LangChain']), S('embeddings', ['embeddings', 'vector database', 'vector databases', 'vector store']),
    // AWS services and other infra
    S('Boto3', ['Boto3']), S('AWS Lambda', ['AWS Lambda'], { cs: ['Lambda'] }), S('Bedrock', ['AWS Bedrock', 'Amazon Bedrock', 'Bedrock']), S('SageMaker', ['SageMaker']),
    S('Athena', [], { cs: ['Athena'] }), S('Ansible', ['Ansible']), S('Nginx', ['Nginx']), S('Linux', [], { cs: ['Linux'] }), S('Bash', [], { cs: ['Bash'] }), S('Git', [], { cs: ['Git'] }),
    S('Cassandra', ['Cassandra']), S('Neo4j', ['Neo4j']), S('Memcached', ['Memcached']), S('Oracle', [], { cs: ['Oracle'] }), S('SQL Server', ['SQL Server', 'MSSQL']),
    // Identity and security
    S('OAuth', ['OAuth', 'OAuth2', 'OpenID Connect'], { cs: ['OIDC'] }), S('SAML', [], { cs: ['SAML'] }), S('SSO', [], { cs: ['SSO'] }),
    // Other frameworks seen in JDs
    S('Marko', [], { cs: ['Marko'] }), S('Vue', ['Vue']), S('Gatsby', ['Gatsby']), S('Remix', [], { cs: ['Remix'] }),
    // Concepts: satisfied by any of the listed skills
    { t: 'cloud', a: ['cloud', 'cloud-native', 'cloud vendor', 'cloud infrastructure', 'cloud platform'], kind: 'concept', by: ['AWS', 'GCP', 'Azure', 'Cloudflare'] },
    { t: 'asynchronous programming', a: ['asynchronous', 'async programming', 'async'], kind: 'concept', by: ['BullMQ', 'Kafka', 'event-driven', 'WebSocket', 'SSE', 'Node.js'] },
    { t: 'CI/CD', a: ['CI/CD', 'CICD', 'continuous integration', 'continuous delivery', 'continuous deployment'], kind: 'concept', by: ['GitHub Actions', 'GitLab CI', 'Jenkins', 'ArgoCD'] },
    // Domains: satisfied when the master file mentions them (profile.domains)
    { t: 'SaaS', a: ['SaaS'], kind: 'domain' },
    { t: 'payments', a: ['payments', 'payment'], kind: 'domain' },
    { t: 'fintech', a: ['fintech'], kind: 'domain' },
    { t: 'ed-tech', a: ['ed-tech', 'edtech'], kind: 'domain' },
    { t: 'real-time', a: ['real-time', 'realtime', 'real time'], kind: 'domain' },
    { t: 'e-commerce', a: ['e-commerce', 'ecommerce'], kind: 'domain' },
    { t: 'analytics', a: ['analytics'], kind: 'domain' },
    { t: 'machine learning', a: ['machine learning'], kind: 'domain' },
  ];
});
