// Pipeline CI/CD GitOps :
// lint + tests -> build image -> scan Trivy -> smoke test -> push Docker Hub
// -> mise à jour du tag dans k8s/overlays/prod -> Argo CD déploie automatiquement
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'mayssadhahri1/taskflow'
        IMAGE_TAG  = "1.0.${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {
        stage('Lint & Tests') {
            agent {
                docker { image 'python:3.12-slim'; reuseNode true }
            }
            steps {
                sh '''
                  python -m venv .venv && . .venv/bin/activate
                  pip install --no-cache-dir -r requirements-dev.txt
                  ruff check .
                  ruff format --check .
                  pytest --junitxml=reports/tests.xml
                '''
            }
            post {
                always { junit 'reports/tests.xml' }
            }
        }

        stage('Validation Kubernetes') {
            steps {
                // Vérifie que les manifestes générés par Kustomize sont valides
                sh '''
                  for env in dev prod; do
                    docker run --rm -v "$PWD":/work -w /work registry.k8s.io/kubectl:v1.34.0 \
                      kustomize k8s/overlays/$env > /tmp/taskflow-$env.yaml
                    docker run --rm -v /tmp:/tmp ghcr.io/yannh/kubeconform:latest \
                      -strict -summary -ignore-missing-schemas /tmp/taskflow-$env.yaml
                  done
                '''
            }
        }

        stage('Build image') {
            steps {
                sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG .'
            }
        }

        stage('Scan Trivy') {
            steps {
                sh '''
                  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                    aquasec/trivy:latest image --exit-code 1 --severity CRITICAL \
                    --ignore-unfixed $IMAGE_NAME:$IMAGE_TAG
                '''
            }
        }

        stage('Smoke test') {
            steps {
                sh '''
                  docker rm -f taskflow-smoke || true
                  docker run -d --name taskflow-smoke -p 8099:8000 \
                    -e DATABASE_URL=sqlite:////tmp/smoke.db $IMAGE_NAME:$IMAGE_TAG
                  for i in $(seq 1 15); do
                    curl -fs http://localhost:8099/health/ready && exit 0
                    sleep 2
                  done
                  docker logs taskflow-smoke
                  exit 1
                '''
            }
            post {
                always { sh 'docker rm -f taskflow-smoke || true' }
            }
        }

        stage('Push Docker Hub') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                                  usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
                    sh '''
                      echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
                      docker push $IMAGE_NAME:$IMAGE_TAG
                      docker logout
                    '''
                }
            }
        }

        stage('GitOps : mise à jour du tag') {
            when { branch 'main' }
            steps {
                // Le pipeline ne déploie pas lui-même : il modifie le dépôt, Argo CD fait le reste
                withCredentials([usernamePassword(credentialsId: 'github-credentials',
                                                  usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                    sh '''
                      sed -i "s/newTag: .*/newTag: \\"$IMAGE_TAG\\"/" k8s/overlays/prod/kustomization.yaml
                      git config user.name "jenkins"
                      git config user.email "jenkins@taskflow.local"
                      git add k8s/overlays/prod/kustomization.yaml
                      git commit -m "deploy: taskflow $IMAGE_TAG [skip ci]" || exit 0
                      git push https://$GIT_USER:$GIT_TOKEN@github.com/mayssadhahri1/taskflow.git HEAD:main
                    '''
                }
            }
        }
    }

    post {
        success { echo "Version ${env.IMAGE_TAG} publiée, Argo CD va la déployer." }
        failure { echo 'Le pipeline a échoué, voir les logs ci-dessus.' }
    }
}
