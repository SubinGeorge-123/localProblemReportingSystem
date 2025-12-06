pipeline {
    agent any

    environment {
        IMAGE_NAME = "subingeorge2000/localproblemreportingsystem"
        IMAGE_TAG = "latest"

        SONAR_HOST_URL = 'https://sonarcloud.io'
        SONAR_TOKEN    = credentials('sonar_token')
        SONAR_KEY      = 'subingeorge-123_localproblemreportingsystem'
        SONAR_ORGANIZATION = 'subingeorge-123'
        EC2_IP = credentials('ec2_ip')
    }

    parameters {
        booleanParam(name: 'DEPLOY_EC2', defaultValue: true, description: 'Deploy to EC2?')
    }

    stages {

        stage('Checkout') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/SubinGeorge-123/localProblemReportingSystem.git',
                    credentialsId: 'github_credential'
            }
        }

        stage('Install dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Build Docker Image & Run Tests') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'django_secret_key', variable: 'SECRET_KEY'),
                        string(credentialsId: 'django_superuser_username', variable: 'SUPERUSER_NAME'),
                        string(credentialsId: 'django_superuser_email', variable: 'SUPERUSER_EMAIL'),
                        string(credentialsId: 'django_superuser_password', variable: 'SUPERUSER_PASS')
                    ]) {
                        try {
                            sh """
                                docker build \\
                                    --build-arg DJANGO_SECRET_KEY=\${SECRET_KEY} \\
                                    --build-arg DJANGO_SUPERUSER_USERNAME=\${SUPERUSER_NAME} \\
                                    --build-arg DJANGO_SUPERUSER_EMAIL=\${SUPERUSER_EMAIL} \\
                                    --build-arg DJANGO_SUPERUSER_PASSWORD=\${SUPERUSER_PASS} \\
                                    -t \${IMAGE_NAME}:\${IMAGE_TAG} .
                            """
                            sh """
                                docker run -d \\
                                    --name test_container \\
                                    -e DJANGO_SECRET_KEY=\${SECRET_KEY} \\
                                    -e DEBUG=True \\
                                    -p 8000:8000 \\
                                    \${IMAGE_NAME}:\${IMAGE_TAG}
                            """
                            sh """
                                # Wait a moment for Django to start
                                sleep 5
                                docker exec test_container python3 manage.py test
                            """
                        } finally {
                            sh """
                                docker stop test_container || true
                                docker rm test_container || true
                            """
                        }
                    }
                }
            }
        }

        stage('Generate Coverage') {
            steps {
                script {
                   sh """
                # Remove old coverage.xml
                rm -f coverage.xml || true

                docker run --rm \
                  -v \${PWD}:/app \
                    -w /app \
                    python:3.11-slim bash -c "
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install coverage
                        coverage run --source='.' manage.py test
                        coverage xml -o coverage.xml
                    "
            """

            // show file to confirm
            sh "ls -la coverage.xml"
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    retry(2) {
                      sh """
                    docker run --rm \
                        -e SONAR_TOKEN=${SONAR_TOKEN} \
                        -v \$PWD:/usr/src \
                        -w /usr/src \
                        sonarsource/sonar-scanner-cli:latest \
                        -Dsonar.projectKey=${SONAR_KEY} \
                        -Dsonar.organization=${SONAR_ORGANIZATION} \
                        -Dsonar.host.url=${SONAR_HOST_URL} \
                        -Dsonar.sources=. \
                        -Dsonar.exclusions=**/venv/**,**/migrations/**,**/django/**,**/botocore/**,**/site-packages/** \
                        -Dsonar.login=\$SONAR_TOKEN \
                        -Dsonar.python.coverage.reportPaths=coverage.xml
                """
                    }
                }
            }
        }

      stage('ZAP Scan') {
            steps {
                script {
                    try {
                        withCredentials([
                            string(credentialsId: 'django_secret_key', variable: 'SECRET_KEY')
                        ]) {
                            sh "docker network create devnet || true"
                            sh "docker rm -f er_scan || true"

                            sh """
                                docker run -d --name er_scan --network devnet \\
                                    -e DJANGO_SECRET_KEY=\${SECRET_KEY} \\
                                    -e DEBUG=True \\
                                    -e ALLOWED_HOSTS="*" \\
                                    \${IMAGE_NAME}:\${IMAGE_TAG} sh -c "python manage.py runserver 0.0.0.0:8000 --noreload"
                            """

                            sh """
                                timeout=60
                                count=0
                                while ! docker exec er_scan curl -s http://localhost:8000/ >/dev/null 2>&1; do
                                    if [ \$count -ge \$timeout ]; then
                                        echo "Django failed to start"
                                        docker logs er_scan
                                        exit 1
                                    fi
                                    echo "Waiting for Django... (\$count seconds)"
                                    sleep 5
                                    count=\$((count + 5))
                                done
                                echo "Django is ready"
                            """

                            sh """
                                docker run --rm --network devnet \\
                                    -v /var/lib/jenkins:/zap/wrk --user root \\
                                    ghcr.io/zaproxy/zaproxy:stable \\
                                    zap-full-scan.py -t http://er_scan:8000 -r /zap/wrk/zap_report.html \\
                                    -m 1 -T 2 -z "-config api.disablekey=true" \\
                                    -I || echo "ZAP scan completed"
                            """
                        }
                    } finally {
                        sh "docker rm -f er_scan || true"
                    }
                }
            }
        }

        stage('Push Docker Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh "docker push \${IMAGE_NAME}:\${IMAGE_TAG}"
                }
            }
        }

stage('Deploy to EC2') {
    steps {
        sshagent(['ec2-key']) {
            withCredentials([
                usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS'),
                string(credentialsId: 'django_secret_key', variable: 'SECRET_KEY'),
                string(credentialsId: 'django_superuser_username', variable: 'SUPERUSER_NAME'),
                string(credentialsId: 'django_superuser_email', variable: 'SUPERUSER_EMAIL'),
                string(credentialsId: 'django_superuser_password', variable: 'SUPERUSER_PASS')
            ]) {
                script {
                    writeFile file: 'deploy.sh', text: """#!/bin/bash
                        set -x
                        
                        # Force logout and login to ensure fresh credentials
                        docker logout
                        echo '${DOCKER_PASS}' | docker login -u '${DOCKER_USER}' --password-stdin
                        
                        # ALWAYS pull latest image (force pull)
                        docker pull ${IMAGE_NAME}:${IMAGE_TAG} --force
                        
                        # Stop and remove ALL containers (force)
                        docker stop localproblemreportingsystem || true
                        docker rm -f localproblemreportingsystem || true
                        
                        # Remove old image to force fresh pull
                        docker rmi ${IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null || true
                        
                        # Create directory for persistent data
                        mkdir -p /home/ubuntu/er_data
                        
                        # Run migrations before starting (optional)
                        docker run --rm -v /home/ubuntu/er_data/db.sqlite3:/app/db.sqlite3 \\
                            -e DJANGO_SECRET_KEY='${SECRET_KEY}' \\
                            -e DEBUG=False \\
                            ${IMAGE_NAME}:${IMAGE_TAG} python manage.py migrate --noinput || true
                        
                        # Run new container with environment variables
                        docker run -d -p 8000:8000 --name localproblemreportingsystem \\
                            --restart unless-stopped \\
                            -e DJANGO_SECRET_KEY='${SECRET_KEY}' \\
                            -e DJANGO_SUPERUSER_USERNAME='${SUPERUSER_NAME}' \\
                            -e DJANGO_SUPERUSER_EMAIL='${SUPERUSER_EMAIL}' \\
                            -e DJANGO_SUPERUSER_PASSWORD='${SUPERUSER_PASS}' \\
                            -e DEBUG=False \\
                            -e ALLOWED_HOSTS='*' \\
                            -v /home/ubuntu/er_data/db.sqlite3:/app/db.sqlite3 \\
                            ${IMAGE_NAME}:${IMAGE_TAG}
                        
                        # Wait and verify
                        sleep 15
                        echo "=== Checking container status ==="
                        docker ps | grep localproblemreportingsystem
                        
                        echo "=== Checking container logs ==="
                        docker logs --tail 20 localproblemreportingsystem || true
                        
                        echo "=== Checking application health ==="
                        timeout 30 bash -c 'until curl -s http://localhost:8000/ >/dev/null; do sleep 2; done' || true
                        
                        echo "Deployment completed!"
                    """
                    
                    sh """
                        chmod +x deploy.sh
                        scp -o StrictHostKeyChecking=no deploy.sh ubuntu@\${EC2_IP}:/tmp/deploy.sh
                        ssh -o StrictHostKeyChecking=no ubuntu@\${EC2_IP} "bash /tmp/deploy.sh"
                    """
                }
            }
        }
    }
}
    }

    post {
        failure {
            echo "❌ Build ${BUILD_TAG} failed."
        }
        success {
            echo "✅ Build ${BUILD_TAG} succeeded."
        }
    }
}