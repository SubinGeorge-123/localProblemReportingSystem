pipeline {
    agent any

    environment {
        IMAGE_NAME = "subin/localproblemreportingsystem"
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
                    try {
                        sh """
                            docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                        """
                        sh "docker run -d --name localProblemReportingSystem -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}"
                        sh "docker exec localProblemReportingSystem python3 manage.py test"
                    }
                    finally {
                        sh """
                            docker stop localProblemReportingSystem || true
                            docker rm localProblemReportingSystem || true
                        """
                    }
                }
            }
        }

//         stage('SonarQube Analysis') {
//     steps {
//         sh """
//             docker run --rm \
//                 -e SONAR_TOKEN=${SONAR_TOKEN} \
//                 -v \$PWD:/usr/src \
//                 -w /usr/src \
//                 sonarsource/sonar-scanner-cli \
//                 -Dsonar.projectKey=${SONAR_KEY} \
//                 -Dsonar.organization=${SONAR_ORGANIZATION} \
//                 -Dsonar.host.url=${SONAR_HOST_URL} \
//                 -Dsonar.sources=. \
//                 -Dsonar.exclusions=**/venv/**,**/migrations/**,**/django/**,**/botocore/**,**/site-packages/** \
//                 -Dsonar.login=\$SONAR_TOKEN \
//                 -Dsonar.python.coverage.reportPaths=coverage.xml
//         """
//     }
// }


stage('ZAP Scan') {
    steps {
        script {
            try {
                sh "docker network create devnet || true"
                sh "docker rm -f er_scan || true"
                
                sh """
                    docker run -d --name er_scan -p 8000:8000 --network devnet ${IMAGE_NAME}:${IMAGE_TAG}
                """

                // Robust wait with timeout
                sh """
                    timeout=180
                    counter=0
                    while ! curl -f -s http://er_scan:8000/ > /dev/null; do
                        if [ \$counter -ge \$timeout ]; then
                            echo "Timeout waiting for Django"
                            exit 1
                        fi
                        echo "Waiting for Django... (\$counter seconds)"
                        sleep 5
                        counter=\$((counter + 5))
                    done
                    echo "Django is ready after \$counter seconds"
                    sleep 10  # Extra safety margin
                """

                // Run ZAP - don't fail build on findings
                sh """
                    docker run --rm --network devnet -v /var/lib/jenkins:/zap/wrk --user root \
                        ghcr.io/zaproxy/zaproxy:stable \
                        zap-full-scan.py -t http://er_scan:8000 -r /zap/wrk/zap_report.html \
                        -m 1 -T 2 -z "-config api.disablekey=true -config scanner.threadPerHost=2" \
                        -I || echo "ZAP scan found issues (this is expected)"
                """
                
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
                        sh """
                            ssh -o StrictHostKeyChecking=no ubuntu@$EC2_IP << EOF
                            set -x
                            docker login -u $DOCKER_USER -p $DOCKER_PASS
                            docker pull subin/localProblemReportingSystem:latest
                            docker rm -f localProblemReportingSystem || true

                            docker run -d -p 8000:8000 --name localProblemReportingSystem \
                                --restart unless-stopped \
                                -v /home/ubuntu/er_data/db.sqlite3:/app/db.sqlite3 \
                                subin/localProblemReportingSystem:latest
EOF
                        """
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
