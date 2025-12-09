pipeline {
    agent any
    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        HARBOR_URL = "10.131.103.92:8090"
        HARBOR_PROJECT = "kp_3"
        TRIVY_OUTPUT_JSON = "trivy-output.json"
    }
    parameters {
        choice(
            name: 'ACTION',
            choices: ['FULL_PIPELINE', 'FRONTEND', 'BACKEND', 'SCALE_ONLY'],
            description: 'Choose which microservice to run'
        )
        string(name: 'FRONTEND_REPLICA', defaultValue: '1', description: 'Frontend replica count')
        string(name: 'BACKEND_REPLICA', defaultValue: '1', description: 'Backend replica count')
        string(name: 'DB_REPLICA', defaultValue: '1', description: 'Database replica count')
    }
    stages {
        stage('Checkout') {
            when { expression { params.ACTION != 'SCALE_ONLY' } }
            steps {
                git 'https://github.com/ThanujaRatakonda/kp_3.git'
            }
        }
        stage('Build Docker Images') {
            when { expression { params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND' || params.ACTION == 'BACKEND' } }
            steps {
                script {
                    def containers = []
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND') containers << [name: 'frontend', folder: 'frontend']
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'BACKEND') containers << [name: 'backend', folder: 'backend']

                    containers.each { c ->
                        echo "Building Docker image for ${c.name}..."
                        sh "docker build -t ${c.name}:${IMAGE_TAG} ./${c.folder}"
                    }
                }
            }
        }
        stage('Scan Docker Images') {
            when { expression { params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND' || params.ACTION == 'BACKEND' } }
            steps {
                script {
                    def containers = []
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND') containers << 'frontend'
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'BACKEND') containers << 'backend'

                    containers.each { img ->
                        echo "Running Trivy scan for ${img}:${IMAGE_TAG}..."
                        sh """
                            trivy image ${img}:${IMAGE_TAG} \
                            --severity CRITICAL,HIGH \
                            --format json \
                            -o ${TRIVY_OUTPUT_JSON}
                        """
                        archiveArtifacts artifacts: "${TRIVY_OUTPUT_JSON}", fingerprint: true
                        def vulnerabilities = sh(script: """
                            jq '[.Results[] |
                                 (.Packages // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH")) +
                                 (.Vulnerabilities // [] | .[]? | select(.Severity=="CRITICAL" or .Severity=="HIGH"))
                                ] | length' ${TRIVY_OUTPUT_JSON}
                        """, returnStdout: true).trim()
                        if (vulnerabilities.toInteger() > 0) {
                            error "CRITICAL/HIGH vulnerabilities found in ${img}!"
                        }
                    }
                }
            }
        }
        stage('Push Images to Harbor') {
            when { expression { params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND' || params.ACTION == 'BACKEND' } }
            steps {
                script {
                    def containers = []
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND') containers << 'frontend'
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'BACKEND') containers << 'backend'

                    containers.each { img ->
                        def fullImage = "${HARBOR_URL}/${HARBOR_PROJECT}/${img}:${IMAGE_TAG}"
                        withCredentials([usernamePassword(credentialsId: 'harbor-creds', usernameVariable: 'HARBOR_USER', passwordVariable: 'HARBOR_PASS')]) {
                            sh "echo \$HARBOR_PASS | docker login ${HARBOR_URL} -u \$HARBOR_USER --password-stdin"
                            sh "docker tag ${img}:${IMAGE_TAG} ${fullImage}"
                            sh "docker push ${fullImage}"
                        }
                        sh "docker rmi ${img}:${IMAGE_TAG} || true"
                    }
                }
            }
        }
        stage('Apply Kubernetes Deployment') {
            when { expression { params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND' || params.ACTION == 'BACKEND' } }
            steps {
                script {
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND') {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/frontend-deployment.yaml"
                        sh "kubectl delete deployment frontend --ignore-not-found"
                        sh "kubectl delete service frontend --ignore-not-found"
                        sh "kubectl apply -f k8s/frontend-deployment.yaml"
                        sh "kubectl rollout status deployment frontend --timeout=120s"
                    }
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'BACKEND') {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/backend-deployment.yaml"
                        sh "kubectl delete deployment backend --ignore-not-found"
                        sh "kubectl delete service backend --ignore-not-found"
                        sh "kubectl apply -f k8s/backend-deployment.yaml"
                        sh "kubectl rollout status deployment backend --timeout=120s"
                    }
                    if (params.ACTION == 'FULL_PIPELINE') {
                        sh "kubectl get pvc shared-pvc || kubectl apply -f k8s/shared-pvc.yaml"
                        sh "kubectl delete statefulset database --ignore-not-found"
                        sh "kubectl delete service database --ignore-not-found"
                        sh "kubectl apply -f k8s/database-statefulset.yaml"
                        sh "kubectl rollout status statefulset database --timeout=180s"
                    }
                }
            }
        }
        stage('Scale Deployments') {
            steps {
                script {
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'FRONTEND') {
                        sh "kubectl scale deployment frontend --replicas=${params.FRONTEND_REPLICA}"
                    }
                    if (params.ACTION == 'FULL_PIPELINE' || params.ACTION == 'BACKEND') {
                        sh "kubectl scale deployment backend --replicas=${params.BACKEND_REPLICA}"
                    }
                    if (params.ACTION == 'FULL_PIPELINE') {
                        sh "kubectl scale statefulset database --replicas=${params.DB_REPLICA}"
                    }
                    if (params.ACTION == 'SCALE_ONLY') {
                        sh "kubectl scale deployment frontend --replicas=${params.FRONTEND_REPLICA}"
                        sh "kubectl scale deployment backend --replicas=${params.BACKEND_REPLICA}"
                        sh "kubectl scale statefulset database --replicas=${params.DB_REPLICA}"
                    }
                    sh "kubectl get deployments"
                    sh "kubectl get statefulset database || true"
                }
            }
        }
    }
}
