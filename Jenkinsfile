pipeline {
    agent any
    
    environment {
        DOCKER_REGISTRY = 'your-registry.com'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        KUBECONFIG = credentials('kubeconfig')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Lint Python') {
                    steps {
                        script {
                            sh '''
                                python3 -m pip install flake8 black isort
                                flake8 src/ --max-line-length=100 --exclude=__pycache__
                                black --check src/
                                isort --check-only src/
                            '''
                        }
                    }
                }
                stage('Security Scan') {
                    steps {
                        script {
                            sh '''
                                python3 -m pip install bandit safety
                                bandit -r src/ -f json -o bandit-report.json || true
                                safety check --json --output safety-report.json || true
                            '''
                        }
                        archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
                    }
                }
            }
        }
        
        stage('Test') {
            steps {
                script {
                    sh '''
                        python3 -m pip install -r requirements.txt
                        python3 -m pytest tests/ --junitxml=test-results.xml --cov=src --cov-report=xml
                    '''
                }
                publishTestResults testResultsPattern: 'test-results.xml'
                publishCoverageReports([
                    [
                        reportType: 'COBERTURA',
                        reportFile: 'coverage.xml'
                    ]
                ])
            }
        }
        
        stage('Build Images') {
            parallel {
                stage('Build API') {
                    steps {
                        script {
                            def apiImage = docker.build("${DOCKER_REGISTRY}/ai-customer-support-api:${IMAGE_TAG}", "-f ops/api/Dockerfile.api .")
                            apiImage.push()
                            apiImage.push("latest")
                        }
                    }
                }
                stage('Build MCP') {
                    steps {
                        script {
                            def mcpImage = docker.build("${DOCKER_REGISTRY}/ai-customer-support-mcp:${IMAGE_TAG}", "-f ops/mcp-postgres-official/Dockerfile ops/mcp-postgres-official/")
                            mcpImage.push()
                            mcpImage.push("latest")
                        }
                    }
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                script {
                    sh '''
                        cd ops
                        docker-compose -f docker-compose-simple.yml up -d
                        sleep 30
                        
                        # Wait for services to be healthy
                        timeout 120 bash -c 'until curl -f http://localhost:8000/health; do sleep 5; done'
                        
                        # Run integration tests
                        python3 ../scripts/test_api_integration.py
                        
                        docker-compose -f docker-compose-simple.yml down
                    '''
                }
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        # Update Kubernetes manifests with new image tags
                        sed -i "s/image: .*/image: ${DOCKER_REGISTRY}\\/ai-customer-support-api:${IMAGE_TAG}/" ops/kubernetes/api-deployment.yaml
                        sed -i "s/image: .*/image: ${DOCKER_REGISTRY}\\/ai-customer-support-mcp:${IMAGE_TAG}/" ops/kubernetes/mcp-deployment.yaml
                        
                        # Apply to staging namespace
                        kubectl apply -f ops/kubernetes/ -n staging
                        
                        # Wait for rollout
                        kubectl rollout status deployment/api-service -n staging --timeout=300s
                        kubectl rollout status deployment/mcp-postgres -n staging --timeout=300s
                    '''
                }
            }
        }
        
        stage('Smoke Tests') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        # Run smoke tests against staging
                        STAGING_URL=$(kubectl get service api-service -n staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
                        curl -f http://${STAGING_URL}/health
                        python3 scripts/test_api.py --url http://${STAGING_URL}
                    '''
                }
            }
        }
        
        stage('Deploy to Production') {
            when {
                allOf {
                    branch 'main'
                    expression { return env.DEPLOY_TO_PROD == 'true' }
                }
            }
            steps {
                input message: 'Deploy to Production?', ok: 'Deploy'
                script {
                    sh '''
                        # Apply to production namespace
                        kubectl apply -f ops/kubernetes/ -n production
                        
                        # Wait for rollout
                        kubectl rollout status deployment/api-service -n production --timeout=300s
                        kubectl rollout status deployment/mcp-postgres -n production --timeout=300s
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    // Send success notification
                    sh 'echo "Deployment successful!" | curl -X POST -H "Content-Type: application/json" -d @- webhook-url'
                }
            }
        }
        failure {
            // Send failure notification
            sh 'echo "Build failed!" | curl -X POST -H "Content-Type: application/json" -d @- webhook-url'
        }
    }
}
