# 🎯 Event-Driven Microservices - Decoupled Helm Charts

This repository contains **4 independent Helm charts** for deploying a microservices architecture with RabbitMQ event-driven communication.

## 📦 Chart Structure

```
helm-charts/
├── rabbitmq/               # RabbitMQ message broker
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── namespace.yaml
│       ├── configmap.yaml
│       ├── deployment.yaml
│       ├── _helpers.tpl
│       
├── mongodb/                # MongoDB NoSQL database
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── namespace.yaml
│       ├── deployment.yaml
│       ├── _helpers.tpl
│       
├── todo-app/               # ASP.NET Core + React frontend
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── namespace.yaml
│       ├── deployment.yaml
│       ├── _helpers.tpl
│       
├── notification-service/   # Python FastAPI consumer
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── namespace.yaml
│       ├── deployment.yaml
│       ├── _helpers.tpl
│       
└── app/                    # (OLD) Monolithic chart - can be deprecated
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
```

## 🚀 Quick Start - Deploy with ArgoCD

Each chart is **independent and deployable separately**. This gives you maximum flexibility for GitOps workflows:

### Option 1: Deploy Individual Charts (Recommended for ArgoCD)

```bash
# Deploy RabbitMQ
helm install rabbitmq helm-charts/rabbitmq/ --namespace microservices --create-namespace

# Deploy MongoDB
helm install mongodb helm-charts/mongodb/ --namespace microservices

# Deploy TodoApp
helm install todo-app helm-charts/todo-app/ --namespace microservices

# Deploy Notification Service
helm install notification-service helm-charts/notification-service/ --namespace microservices
```

### Option 2: Deploy All at Once (Quick Testing)

```bash
# Using Helm chart loop
for chart in helm-charts/{rabbitmq,mongodb,todo-app,notification-service}; do
  helm install $(basename $chart) $chart --namespace microservices --create-namespace
done
```

## 📋 ArgoCD Configuration Examples

### Individual ArgoCD Applications (Recommended)

**argocd-rabbitmq.yaml:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: rabbitmq
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR-REPO
    targetRevision: main
    path: helm-charts/rabbitmq
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**argocd-mongodb.yaml:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mongodb
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR-REPO
    targetRevision: main
    path: helm-charts/mongodb
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**argocd-todo-app.yaml:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: todo-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR-REPO
    targetRevision: main
    path: helm-charts/todo-app
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**argocd-notification-service.yaml:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: notification-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR-REPO
    targetRevision: main
    path: helm-charts/notification-service
  destination:
    server: https://kubernetes.default.svc
    namespace: microservices
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## ✅ Chart Details

### 1. RabbitMQ Chart (rabbitmq/)

**Deploys:**
- RabbitMQ 4.2.1 (Latest LTS)
- ConfigMap with RabbitMQ configuration
- Service exposing ports: 5672 (AMQP), 15672 (Management UI), 15691/15692 (Metrics)
- Liveness & Readiness probes
- Resource limits

**Key Values:**
```yaml
rabbitmq:
  image: rabbitmq:4.2.1-management
  port: 5672
  managementPort: 15672
  metricsPort: 15691
  prometheusPort: 15692
  auth:
    user: guest
    password: guest
```

### 2. MongoDB Chart (mongodb/)

**Deploys:**
- MongoDB 7.0
- Service exposing port 27017
- Liveness & Readiness probes
- Resource limits

**Key Values:**
```yaml
mongodb:
  image: mongo:7.0
  port: 27017
```

### 3. Todo App Chart (todo-app/)

**Deploys:**
- ASP.NET Core 3.1 application with embedded React UI
- LoadBalancer service on port 5000
- Security context (runAsUser: 1000)
- Liveness & Readiness probes
- All environment variables configured

**Key Values:**
```yaml
todoApp:
  image:
    repository: dotnet-docker-todo-app
    tag: latest
  port: 5000
  env:
    ASPNETCORE_ENVIRONMENT: Production
    TODO_APP_MongoSettings__ConnectionString: "mongodb://mongodb:27017"
    TODO_APP_RabbitMQ__Host: "rabbitmq"
```

### 4. Notification Service Chart (notification-service/)

**Deploys:**
- Python FastAPI application
- LoadBalancer service on port 8000
- Liveness & Readiness probes (/health, /readiness)
- All environment variables configured

**Key Values:**
```yaml
notificationService:
  image:
    repository: notification-service
    tag: latest
  port: 8000
  env:
    RABBITMQ_HOST: "rabbitmq"
    MONGODB_URI: "mongodb://mongodb:27017"
```

## 📊 Architecture

```
                        ┌─────────────────┐
                        │   Todo App      │
                        │  (ASP.NET Core) │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │   RabbitMQ      │
                        │  (Event Broker) │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
            ┌───────▼──────┐        ┌────────▼──────┐
            │   MongoDB    │        │Notification   │
            │  (Todos DB)  │        │Service(Python)│
            └──────────────┘        └────────┬──────┘
                                            │
                                    ┌───────▼──────┐
                                    │   MongoDB    │
                                    │(Notifications)│
                                    └──────────────┘
```

## 🔄 Service Communication

1. **Todo App** creates a todo → publishes event to RabbitMQ
2. **RabbitMQ** routes event to queue (task_events exchange)
3. **Notification Service** consumes from queue → saves to MongoDB
4. **Notification Service UI** displays notifications in real-time

## 🛠️ Customization

Each chart has independent `values.yaml` for customization:

```bash
# Deploy with custom values
helm install rabbitmq helm-charts/rabbitmq/ \
  --namespace microservices \
  --values custom-values.yaml

# Or override specific values
helm install rabbitmq helm-charts/rabbitmq/ \
  --set rabbitmq.replicaCount=3 \
  --set rabbitmq.persistence.enabled=true
```

## 📝 Deployment Sequence (Important!)

Charts should be deployed in this order for optimal startup:
1. **RabbitMQ** (needed by both services)
2. **MongoDB** (needed by both services)
3. **Todo App** (can start once RabbitMQ/MongoDB ready)
4. **Notification Service** (can start once RabbitMQ/MongoDB ready)

**Note:** With ArgoCD, services are resilient to startup order mismatches due to retry logic.

## 🎯 ArgoCD Benefits

By using separate Helm charts:

✅ **Independent Deployments** - Deploy each service separately  
✅ **Different Update Cadences** - Update services independently  
✅ **Team Ownership** - Different teams can manage different services  
✅ **Easy Rollbacks** - Rollback individual services  
✅ **GitOps Flexibility** - Track each service in separate paths  
✅ **Multi-Environment** - Easy to deploy different configs per environment  

## 🔍 Monitoring & Troubleshooting

```bash
# Check all deployments
kubectl get all -n microservices

# Check service connectivity
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  sh -c "nc -z rabbitmq 5672 && echo 'RabbitMQ OK' || echo 'RabbitMQ FAILED'"

# View logs
kubectl logs -f -n microservices -l app=todo-app
kubectl logs -f -n microservices -l app=notification-service

# Access RabbitMQ Management UI
kubectl port-forward -n microservices svc/rabbitmq 15672:15672
# Open http://localhost:15672 (guest/guest)
```

## 📄 License

MIT License - See LICENSE file

## 👥 Support

For issues and questions, please open an issue on GitHub.
