pipeline {
    agent any

    environment {
        # Jenkins credentials IDs
        GITHUB_TOKEN = credentials('github-token')
        SECRET_KEY = credentials('django-secret-key')
        SONAR_TOKEN = credentials('sonarqube-token')
        
        # Django environment
        DJANGO_ALLOWED_HOSTS = 'localhost,127.0.0.1,18.209.69.93,ec2-18-209-69-93.compute-1.amazonaws.com'
        DJANGO_CSRF_TRUSTED_ORIGINS = 'http://18.209.69.93,http://ec2-18-209-69-93.compute-1.amazonaws.com'
        DEBUG = 'False'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/SubinGeorge-123/localProblemReportingSystem.git',
                    credentialsId: 'github-token'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                python3 -m pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Django Tests') {
            steps {
                sh '''
                export SECRET_KEY=$SECRET_KEY
                export DJANGO_ALLOWED_HOSTS=$DJANGO_ALLOWED_HOSTS
                export DJANGO_CSRF_TRUSTED_ORIGINS=$DJANGO_CSRF_TRUSTED_ORIGINS
                export DEBUG=$DEBUG

                python manage.py test
                python tests.py
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                    sonar-scanner \
                      -Dsonar.projectKey=localProblemReportingSystem \
                      -Dsonar.projectName="Local Problem Reporting System" \
                      -Dsonar.sources=. \
                      -Dsonar.host.url=https://sonarcloud.io \
                      -Dsonar.login=$SONAR_TOKEN
                    '''
                }
            }
        }

        stage('OWASP ZAP Scan') {
            steps {
                sh '''
                # Pull the ZAP Docker image if not exists
                docker pull owasp/zap2docker-stable

                # Run baseline scan against the local Django server
                # Make sure your Django server is running at localhost:8000
                docker run -t owasp/zap2docker-stable zap-baseline.py -t http://localhost:8000
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                docker build --build-arg SECRET_KEY=$SECRET_KEY \
                             --build-arg DJANGO_ALLOWED_HOSTS=$DJANGO_ALLOWED_HOSTS \
                             --build-arg DJANGO_CSRF_TRUSTED_ORIGINS=$DJANGO_CSRF_TRUSTED_ORIGINS \
                             -t localproblemreportingapp .
                '''
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh '''
                # Stop existing container if exists
                docker stop localproblemreportingapp || true
                docker rm localproblemreportingapp || true

                # Run new container with SQLite DB
                docker run -d -p 80:8000 \
                  -e SECRET_KEY=$SECRET_KEY \
                  -e DJANGO_ALLOWED_HOSTS=$DJANGO_ALLOWED_HOSTS \
                  -e DJANGO_CSRF_TRUSTED_ORIGINS=$DJANGO_CSRF_TRUSTED_ORIGINS \
                  -e DEBUG=$DEBUG \
                  --name localproblemreportingapp localproblemreportingapp
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished.'
        }
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
