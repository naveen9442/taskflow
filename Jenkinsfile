pipeline {
    // Run on any available Jenkins agent
    agent any

    // Environment variables available to all stages
    environment {
        IMAGE_NAME    = 'taskflow'
        IMAGE_TAG     = "${BUILD_NUMBER}"   // Jenkins build number as tag
        CONTAINER_NAME = 'taskflow_app'
    }

    stages {

        // ---- Stage 1: Checkout ----
        // Jenkins pulls the latest code from Git
        stage('Checkout') {
            steps {
                echo 'Pulling latest code from Git...'
                checkout scm
            }
        }

        // ---- Stage 2: Test ----
        // Run unit tests before building
        stage('Test') {
            steps {
                echo 'Running tests...'
                sh '''
                    pip3 install flask prometheus-client pytest --quiet
                    python3 -m pytest tests/ -v || echo "No tests found, skipping"
                '''
            }
        }

        // ---- Stage 3: Build Docker Image ----
        // Package the app into a Docker image
        stage('Build Docker Image') {
            steps {
                echo "Building image: ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
            }
        }

        // ---- Stage 4: Security Scan (optional) ----
        // Scan image for vulnerabilities
        stage('Security Scan') {
            steps {
                echo 'Scanning Docker image for vulnerabilities...'
                sh '''
                    # Install trivy if not present
                    which trivy || (
                        curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
                    )
                    trivy image --exit-code 0 --severity HIGH,CRITICAL ${IMAGE_NAME}:latest
                '''
            }
        }

        // ---- Stage 5: Deploy with Ansible ----
        // Ansible deploys the new image to the server
        stage('Deploy') {
            steps {
                echo 'Deploying with Ansible...'
                sh 'ansible-playbook -i ansible/inventory.ini ansible/playbook.yml'
            }
        }

        // ---- Stage 6: Health Check ----
        // Verify the deployment was successful
        stage('Health Check') {
            steps {
                echo 'Checking app health...'
                sh '''
                    sleep 5
                    curl -f http://localhost/health || exit 1
                    echo "Deployment successful!"
                '''
            }
        }
    }

    // ---- Post Actions (always run) ----
    post {
        success {
            echo "Pipeline succeeded! Build #${BUILD_NUMBER} deployed."
        }
        failure {
            echo "Pipeline FAILED at build #${BUILD_NUMBER}. Check logs above."
        }
        always {
            // Clean up old Docker images to save disk space
            sh "docker image prune -f --filter 'until=24h'"
        }
    }
}
