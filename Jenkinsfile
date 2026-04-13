pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                git branch: 'master', 
                    url: 'https://github.com/naveen9442/taskflow.git',
                    credentialsId: 'github-token'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t taskflow:${BUILD_NUMBER} .'
                sh 'docker tag taskflow:${BUILD_NUMBER} taskflow:latest'
            }
        }
        
        stage('Deploy') {
            steps {
                sh 'docker stop taskflow_app || true'
                sh 'docker rm taskflow_app || true'
                sh 'docker run -d --name taskflow_app -p 5000:5000 taskflow:latest'
            }
        }
        
        stage('Health Check') {
            steps {
                sh 'sleep 5'
                sh 'curl -f http://localhost:5000/health || exit 1'
            }
        }
    }
    
    post {
        success {
            echo '✅ Deployment Successful!'
            echo 'App is running at: http://192.168.133.131:5000'
        }
        failure {
            echo '❌ Deployment Failed!'
        }
        always {
            sh 'docker image prune -f --filter until=24h || true'
        }
    }
}
