pipeline {
    agent any
    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        HARBOR_URL = "10.131.103.92:8090"
        HARBOR_PROJECT = "kp_4"
        TRIVY_OUTPUT_JSON = "trivy-output.json"
    }
    parameters {
        choice(
            name: 'MICROSERVICE',
            choices: ['FULL_PIPELINE', 'FRONTEND', 'BACKEND', 'SCALE_ONLY'],
            description: 'Choose microservice to update or scale only'
        )
        string(name: 'FRONTEND_REPLICA', defaultValue: '1', description: 'Frontend replicas')
        string(name: 'BACKEND_REPLICA', defaultValue: '1', description: 'Backend replicas')
        string(name: 'DB_REPLICA', defaultValue: '1', description: 'Database replicas')
    }

    stages {

        stage('Checkout') {
            when { expression { params.MICROSERVICE != 'SCALE_ONLY' } }
            steps {
                git 'https://github.com/ThanujaRatakonda/kp_4.git'
            }
        }

        stage('Build Docker Images') {
            when { expression { params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND', 'BACKEND'] } }
            steps {
                script {
                    def containers = []
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND']) {
                        containers << [name: "frontend", folder: "frontend"]
                    }
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'BACKEND']) {
                        containers << [name: "backend", folder: "backend"]
                    }

                    containers.each { c ->
                        echo "Building Docker image for ${c.name}..."
                        sh "docker build -t ${c.name}:${IMAGE_TAG} ./${c.folder}"
                    }
                }
            }
        }

        stage('Scan Docker Images') {
            when { expression { params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND', 'BACKEND'] } }
            steps {
                script {
                    def containers = []
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND']) containers << "frontend"
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'BACKEND']) containers << "backend"

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
            when { expression { params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND', 'BACKEND'] } }
            steps {
                script {
                    def containers = []
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND']) containers << "frontend"
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'BACKEND']) containers << "backend"

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
            when { expression { params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND', 'BACKEND'] } }
            steps {
                script {
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'FRONTEND']) {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/frontend-deployment.yaml"
                    }
                    if (params.MICROSERVICE in ['FULL_PIPELINE', 'BACKEND']) {
                        sh "sed -i 's/__IMAGE_TAG__/${IMAGE_TAG}/g' k8s/backend-deployment.yaml"
                    }

                    sh """
                        if [ "${params.MICROSERVICE}" = "FULL_PIPELINE" ] || [ "${params.MICROSERVICE}" = "FRONTEND" ]; then
                            kubectl delete deployment frontend --ignore-not-found
                            kubectl delete service frontend --ignore-not-found
                        fi
                        if [ "${params.MICROSERVICE}" = "FULL_PIPELINE" ] || [ "${params.MICROSERVICE}" = "BACKEND" ]; then
                            kubectl delete deployment backend --ignore-not-found
                            kubectl delete service backend --ignore-not-found
                        fi
                        if [ "${params.MICROSERVICE}" = "FULL_PIPELINE" ]; then
                            kubectl delete statefulset database --ignore-not-found
                            kubectl delete service database --ignore-not-found
                        fi
                        kubectl get pvc shared-pvc || kubectl apply -f k8s/shared-pvc.yaml
                        kubectl apply -f k8s/
                    """
                }
            }
        }

        stage('Scale Deployments') {
            steps {
                script {
                    sh """
                        kubectl scale deployment frontend --replicas=${params.FRONTEND_REPLICA}
                        kubectl scale deployment backend --replicas=${params.BACKEND_REPLICA}
                        kubectl scale statefulset database --replicas=${params.DB_REPLICA}
                        kubectl get deployments
                    """
                }
            }
        }
    }
}
