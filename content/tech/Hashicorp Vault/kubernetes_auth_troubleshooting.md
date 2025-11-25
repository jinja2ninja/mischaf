---
title: "Kubernetes Auth Troubleshooting"
date: 2025-11-23
lastmod: 2025-11-23
draft: true
---
# Vault Kubernetes Auth Troubleshooting
I recently went down the rabbit hole of setting up the External Secrets Operator to sync secrets from my Openbao instance. For those who aren't aware, Openbao is an open source fork of Hashicorp Vault. It's close to, if not completely API compatible, so for the purposes of this post, we can just refer to Vault or Openbao interchangably. 

The External Secrets Operator supports a handful of authentication methods to Vault, some of which are a lot easier to get up and running than others. The one that's probably the most difficult to set up is Kubernetes authentication, but that's also the most secure method, and what you should probably be using in 99.99% of production environments. 

I spent a few days getting my ass kicked by errors trying to set this up initially, so I wrote this post up as a place to track some of my thoughts on the process, as well as to store and share how I got it working. 

If you're just looking for the working config, skip down to the bottom of the page.

## Vault Documentation
The first place I looked was the [documentation](https://developer.hashicorp.com/vault/docs/auth/kubernetes) from Hashicorp. As per usual, the documentation is pretty good, but lacks some concrete end-to-end examples for the uninitiated. 
They list a few ways to set this up, and the location of your Vault (in the same kubernetes cluster as the ESO, or external to it), makes that list of options even more complex.
With that said, my requirement was to not use a long lived JWT, which leaves us with either using 
  - A [local service account token](https://developer.hashicorp.com/vault/docs/auth/kubernetes) (within the same k8s cluster as the Vault)
  - The [Vault Client's token](https://developer.hashicorp.com/vault/docs/auth/kubernetes) (outside of the cluster)
The documentation tells you most of what you need to know, but without knowing the exact parameters for the Vault backend role, I went through a lot of trial and error to find a working setup.
So I set everything up to the best of my understanding of the docs, and started hitting 403 errors when I created an external secret.
## Troubleshooting
#### Vault Client Logs
The first and easiest place to look is in the Vault Client logs (External Secrets Operator in this case). 
With the External Secrets Operator, we can find these with
```
kubectl -n external-secrets logs -l app.kubernetes.io/instance=external-secrets
```
This will contain logs from some other pods in the deployment, but its easy enough to find the authentication errors. In my case, they looked like this at one point while I was getting auth issues
```
{"level":"error","ts":1763910667.5410411,"msg":"Reconciler error","controller":"externalsecret","controllerGroup":"external-secrets.io","controllerKind":"ExternalSecret","ExternalSecret":{"name":"test-secret","namespace":"external-secrets"},"namespace":"external-secrets","name":"test-secret","reconcileID":"b48b0c8d-4ad1-4b20-8fe2-ecbca8506149","error":"error processing spec.dataFrom[0].extract, err: unable to log in to auth method: unable to log in with Kubernetes auth: Error making API request.\n\nURL: PUT http://10.0.0.17:8200/v1/auth/kubernetes/login\nCode: 403. Errors:\n\n* permission denied","stacktrace":"sigs.k8s.io/controller-runtime/pkg/internal/controller.(*Controller[...]).reconcileHandler\n\t/home/runner/go/pkg/mod/sigs.k8s.io/controller-runtime@v0.22.3/pkg/internal/controller/controller.go:474\nsigs.k8s.io/controller-runtime/pkg/internal/controller.(*Controller[...]).processNextWorkItem\n\t/home/runner/go/pkg/mod/sigs.k8s.io/controller-runtime@v0.22.3/pkg/internal/controller/controller.go:421\nsigs.k8s.io/controller-runtime/pkg/internal/controller.(*Controller[...]).Start.func1.1\n\t/home/runner/go/pkg/mod/sigs.k8s.io/controller-runtime@v0.22.3/pkg/internal/controller/controller.go:296"}
```
This is a decent lead, it at least lets me know that the reason for failure is a 403 (unauthorized). Depending on your use case for Kubernetes auth, your client may or may not produce helpful logs. Additionally, we don't know why we got a 403. So let's dive a little deeper.

#### Vault Audit Logs
**Note** I provide some raw JWT tokens in this section. This was from a test environment that has since been spun down. Under normal circumstances, these JWT tokens should be treated as extremely sensitive secrets.
Vault provides several mechanisms for audit logging such as stdout and file. I set up file based audit logging in the Vault config, which puts files at `/vault/log/audit.log` in my test Vault container. Looking at these logs provides about the same information, we can see that we got a 403, but we don't know *why*. These logs do show the JWT token used, but they're hashed by the Vault by default (normally this is a good thing). For debugging, we can set the audit device to show raw logs with the `log_raw` option. 

```
vault audit enable file file_path=/vault/logs/audit.log log_raw=true
```

With that turned on, we can see the JWT in the audit log line.
```
{"auth":{"policy_results":{"allowed":true},"token_type":"default"},"error":"permission denied","request":{"data":{"jwt":"eyJhbGciOiJSUzI1NiIsImtpZCI6ImhNMUVOejVPeFlKWmNqZEgzY0tqZl9UQjhmeUttZVd3TmFoWkdrckRGTlEifQ.eyJhdWQiOlsidmF1bHQiXSwiZXhwIjoxNzYzOTE0NTA5LCJpYXQiOjE3NjM5MTM5MDksImlzcyI6Imh0dHBzOi8va3ViZXJuZXRlcy5kZWZhdWx0LnN2Yy5jbHVzdGVyLmxvY2FsIiwianRpIjoiZmViYTliYjktYjI0OC00OWIyLWIwNGEtMDdhMjRkZjBhNTk1Iiwia3ViZXJuZXRlcy5pbyI6eyJuYW1lc3BhY2UiOiJleHRlcm5hbC1zZWNyZXRzIiwic2VydmljZWFjY291bnQiOnsibmFtZSI6InZhdWx0LWF1dGgtZXNvLXRlc3QiLCJ1aWQiOiI3NGYwYjE3OS1kZDk1LTRmM2MtYTEyNS1iOGY2MDI1YjllMzgifX0sIm5iZiI6MTc2MzkxMzkwOSwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmV4dGVybmFsLXNlY3JldHM6dmF1bHQtYXV0aC1lc28tdGVzdCJ9.VTGQ9XbfCCCzIokQeF69z4BZLhqBIdKeQeykRGjwDjduExqO3wfpMWeemod2a8muMlt2lG31Z0hvE2d4GMd4N4fVJoTROEL9Rb7QtUzyD49rxE0ja_UKsCN7WMEWuvcXgLL0FPo0V8R81RiJd9hUieJCWVXgOgjM4lx3fztn6k-SQCHf4u0pMq9ulbQTQzlW4QYhREKzPaRwaCYkyPYKG50rcB7ePsVjEEkfSuqAMaskG4ak_wo6lrWw-1kncGVoeB-KB6PaisT6yYn3yhrzkGyNT4IRkTkzX_S-CfcXLKX5ah_VzKgpUdQ5ftCtaV_geWqArsdqGMfZQfOVVQc4vA","role":"external-secrets"},"headers":{"user-agent":["Go-http-client/1.1"]},"id":"87267c3e-3133-2356-a9dc-52bff0a4ff50","mount_accessor":"auth_kubernetes_ea6faaa8","mount_class":"auth","mount_point":"auth/kubernetes/","mount_running_version":"v0.23.1+builtin","mount_type":"kubernetes","namespace":{"id":"root"},"operation":"update","path":"auth/kubernetes/login","remote_address":"10.0.0.80","remote_port":52580},"time":"2025-11-23
```
We can then take that jwt over to something like https://jwt.io, and see what its parameters look like. This one produces the following:
```
{
  "aud": [
    "vault"
  ],
  "exp": 1763914509,
  "iat": 1763913909,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "jti": "feba9bb9-b248-49b2-b04a-07a24df0a595",
  "kubernetes.io": {
    "namespace": "external-secrets",
    "serviceaccount": {
      "name": "vault-auth-eso-test",
      "uid": "74f0b179-dd95-4f3c-a125-b8f6025b9e38"
    }
  },
  "nbf": 1763913909,
  "sub": "system:serviceaccount:external-secrets:vault-auth-eso-test"
}
```
This can be extremely useful to compare against the Vault config. Several things need to match up:
- The bound service account in the Vault role needs to match the service account listed in the JWT
- The namespace of the service account needs to be in the Vault Role's bound namespaces 
- The service account needs the correct cluster role binding
- The audience needs to match up with the Vault role (or you may need to completely omit this).
    - In my specific case, I had the audience claim set to `vault` on both sides. This still didn't seem to work, but after some research, I realized that for Kubernetes to allow the token review, I also needed a second audience of `https://kubernetes.default.svc.cluster.local` on the Vault Client config (External Secrets Operator)
Additional things to look for and consider:
- Can the Vault reach the kubernetes API address you used in the backend config? - `10.0.0.75:6443` in my case. Test this by connecting to the Vault via kubectl exec, or a regular shell depending on how to have it set up. `nc -vz 10.0.0.75 6443` outside of kubernetes in my example, or `nc -vz kubernetes.default.svc.cluster.local 443` in kubernetes. If this command hangs, you need to get TCP connectivity to the Kubernetes API from the Vault working.
- Did you typo any role names, namespaces, audience claim etc? This sounds obvious, but I've had single letter typos take me hours to discover with other issues in the past. This is a simple check that can save you from massive unnecessary headaches.
- If you're debugging this in a production environment, spin up a lab and gain a better understanding of how this works there. You can very easily spin up Vault in docker or via its helm chart, and get a working test cluster with [Kind](https://kind.sigs.k8s.io/). Having a safe place to test is not only more secure, but also a lot less stressful, and it typically allows you to fail faster (which ultimately lets you succeed faster).
## Working Config
After spending a few days spelunking in Vault Kubernetes auth debugging, I figured out how to get authentication without a long-lived token working in a few different setups. This test setup should work with minimal changes, just make sure the Kubernetes Host matches if running the Vault outside of Kubernetes.
#### Vault Outside of Kubernetes
Vault Terraform
```
resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
}


resource "vault_kubernetes_auth_backend_config" "this" {
  backend                = vault_auth_backend.kubernetes.path
  kubernetes_host        = "https://10.0.0.75:6443"
  kubernetes_ca_cert     = "-----BEGIN CERTIFICATE-----\nMIIBdjCCAR2gAwIBAgIBADAKBggqhkjOPQQDAjAjMSEwHwYDVQQDDBhrM3Mtc2Vy\ndmVyLWNhQDE3NjI1NDc0OTYwHhcNMjUxMTA3MjAzMTM2WhcNMzUxMTA1MjAzMTM2\nWjAjMSEwHwYDVQQDDBhrM3Mtc2VydmVyLWNhQDE3NjI1NDc0OTYwWTATBgcqhkjO\nPQIBBggqhkjOPQMBBwNCAATIGlmRaMPim5Rj0LxMalA+O4WXMhf8y5lfeWDe+5NR\nGzQGbgM1xz6aPGOTnEVowohFgQJ8GneCH00T9sFePlw1o0IwQDAOBgNVHQ8BAf8E\nBAMCAqQwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUSt8C6YtfD4J5PkeDdf6P\nsKFtAL4wCgYIKoZIzj0EAwIDRwAwRAIgcuN55paQ0/kVJfDALGhd+GtRO4TU7QCx\n4l8NJFOMFvACIB5p7wwSz+WC+/amBT9EeCRN6TVnZ2oue5rw4p1OvCTY\n-----END CERTIFICATE-----"
  disable_local_ca_jwt   = true
}

resource "vault_kubernetes_auth_backend_role" "external-secrets" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "external-secrets"
  bound_service_account_names      = ["vault-auth-eso-test"]
  bound_service_account_namespaces = ["external-secrets"]
  token_ttl                        = 3600
  token_policies                   = ["default", "external-secrets"]
  audience                         = "vault"
}


resource "vault_policy" "external-secrets" {
  name = "external-secrets"

  policy = <<EOT
path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/*" {
  capabilities = ["read", "list", "delete"]
}
EOT
}
```
ESO Yaml
```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: role-tokenreview-binding
  namespace: external-secrets
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
  - kind: ServiceAccount
    name: vault-auth-eso-test
    namespace: external-secrets
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault-auth-eso-test
  namespace: external-secrets
---
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: vault-backend-test
spec:
  provider:
    vault:
      server: "http://10.0.0.17:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: vault-auth-eso-test
            audiences:
              - "vault"
              - "https://kubernetes.default.svc.cluster.local"
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: test-secret
  namespace: external-secrets
spec:
  refreshInterval: "1s"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: test-secret
  dataFrom:
  - extract:
      key: test/foo
```
#### Vault In Kubernetes
Vault Terraform
```
resource "vault_auth_backend" "kubernetes" {
  type = "kubernetes"
}

data "kubernetes_secret" "vault_tokenreview" {
  metadata {
    name      = "vault-tokenreview-token"
    namespace = "external-secrets"
  }
}

resource "vault_kubernetes_auth_backend_config" "this" {
  backend                = vault_auth_backend.kubernetes.path
  kubernetes_host        = "https://kubernetes.default.svc.cluster.local"
}

resource "vault_kubernetes_auth_backend_role" "external-secrets" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "external-secrets"
  bound_service_account_names      = ["vault-auth-eso"]
  bound_service_account_namespaces = ["external-secrets"]
  token_ttl                        = 3600
  token_policies                   = ["default", "external-secrets"]
  audience                         = "vault"
}

resource "vault_policy" "external-secrets" {
  name = "external-secrets"

  policy = <<EOT
path "secret/data/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/*" {
  capabilities = ["read", "list", "delete"]
}
EOT
}
```
ESO Yaml
```
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: role-tokenreview-binding
  namespace: external-secrets
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:auth-delegator
subjects:
  - kind: ServiceAccount
    name: vault-auth-eso
    namespace: external-secrets
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vault-auth-eso
  namespace: external-secrets
---
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "https://vault.mischaf.us"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: vault-auth-eso
            audiences:
              - vault
---
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: test-secret
  namespace: external-secrets
spec:
  refreshInterval: "1s"
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: test-secret
  dataFrom:
  - extract:
      key: test/foo
```
