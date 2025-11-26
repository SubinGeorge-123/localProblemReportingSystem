pipeline {
    agent any

    environment {
        IMAGE_NAME = "subingeorge2000/localproblemreportingsystem"
        IMAGE_TAG = "latest"

        DJANGO_SUPERUSER_USERNAME = credentials('django_superuser_username')
        DJANGO_SUPERUSER_EMAIL    = credentials('django_superuser_email')
        DJANGO_SUPERUSER_PASSWORD = credentials('django_superuser_password')

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
                        string(credentialsId: 'django_superuser_username', variable: 'DJANGO_SUPERUSER_USERNAME'),
                        string(credentialsId: 'django_superuser_email', variable: 'DJANGO_SUPERUSER_EMAIL'),
                        string(credentialsId: 'django_superuser_password', variable: 'DJANGO_SUPERUSER_PASSWORD')
                    ]) {
                        try {
                            sh """
                                docker build \
                                --build-arg DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME \
                                --build-arg DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL \
                                --build-arg DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD \
                                -t ${IMAGE_NAME}:${IMAGE_TAG} .
                            """
                            sh "docker run -d --name test_container -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}"
                            sh "docker exec test_container python3 manage.py test"
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
                # Remove old file first to avoid permission mismatch
                rm -f coverage.xml || true

                # Run coverage as the Jenkins user (not root)
                docker run --rm \
                    -u \$(id -u):\$(id -g) \
                    -v \${PWD}:/app \
                    -w /app \
                    python:3.11-slim \
                    bash -c "
                        pip install -r requirements.txt
                        pip install coverage
                        coverage run --source='.' manage.py test
                        coverage xml -o coverage.xml
                    "
            """

            # Show final permissions
            sh "ls -la coverage.xml"
        }
    }
}

stage('SonarQube Analysis') {
    steps {
        script {
            retry(2) { // retry up to 2 times
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
                // create network and cleanup any prior leftover container
                sh "docker network create devnet || true"
                sh "docker rm -f er_scan || true"

                // Run the app container for scanning with --noreload
                sh """
                    docker run -d --name er_scan --network devnet \
                        -e ALLOWED_HOSTS="*" \
                        ${IMAGE_NAME}:${IMAGE_TAG} sh -c "python manage.py runserver 0.0.0.0:8000 --noreload"
                """

                // Wait for Django to become healthy by curling localhost inside the container
                sh """
                    timeout=180
                    counter=0
                    while ! docker exec er_scan sh -c 'curl -f -s http://localhost:8000/ >/dev/null'; do
                        if [ \$counter -ge \$timeout ]; then
                            echo "Timeout waiting for Django (after \$counter seconds)"
                            echo "=== er_scan logs ==="
                            docker logs er_scan || true
                            echo "=== end logs ==="
                            exit 1
                        fi
                        echo "Waiting for Django... (\$counter seconds)"
                        sleep 5
                        counter=\$((counter + 5))
                    done
                    echo "Django is ready after \$counter seconds"
                    sleep 5
                """

                // Run ZAP scan
                sh """
                    docker run --rm --network devnet \
                        -v /var/lib/jenkins:/zap/wrk --user root \
                        ghcr.io/zaproxy/zaproxy:stable \
                        zap-full-scan.py -t http://er_scan:8000 -r /zap/wrk/zap_report.html \
                        -m 1 -T 2 -z "-config api.disablekey=true -config scanner.threadPerHost=2" \
                        -I || echo "ZAP scan found issues (this is expected)"
                """
            } finally {
                // Remove the scan app container
                sh "docker rm -f er_scan || true"
            }
        }
    }
}


        stage('Push Docker Image to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin'
                    sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                }
            }
        }

        stage('Deploy to EC2') {
            when {
                expression { params.DEPLOY_EC2 }
            }
            steps {
                sshagent(['ec2-key']) {
                    withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh '''
                            ssh -o StrictHostKeyChecking=no ubuntu@$EC2_IP << EOF
                            set -x
                            docker login -u $DOCKER_USER -p $DOCKER_PASS
                            docker pull ${IMAGE_NAME}:${IMAGE_TAG}

                            # Stop old container
                            docker rm -f localproblemreportingsystem || true

                            # Run new container with persistent DB
                            docker run -d -p 8000:8000 --name localproblemreportingsystem \
                                --restart unless-stopped \
                                -v /home/ubuntu/er_data/db.sqlite3:/app/db.sqlite3 \
                                ${IMAGE_NAME}:${IMAGE_TAG}
EOF
                        '''
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
