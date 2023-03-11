---
title: "Vault on Kubernetes"
date: 2023-02-14T07:20:31-08:00
lastmod: 2023-02-15T06:31:00-00:00
draft: false
---

# Hashicorp Vault

I have spent quite a bit of time over the past 6 months setting up Hashicorp Vault at work. Its been a fun experience, and I have learned a lot. I'm always a fan of running whatever I run at work in my homelab, and Vault has really proven to be a useful tool. Recently, I've been playing around with Kubernetes again, and figured Vault would be a great place to store my Kubernetes secrets. In this post, I'll try to outline how I set up Vault on my cluster, and how I use it with other apps on the cluster.

---

## Prerequisites

- I opted to use AWS KMS to unseal the Vault, this requires creating a KMS key on AWS first. You don't need to do this if you're fine manually 
unsealing the vault. To me this is worth the cost of slightly less than a dollar a month. I'm not going to get into the weeds about how to create a 
KMS key. You basically just need the key, and an IAM role and credentials. There are plenty of good guides out there like [this one](https://blogs.halodoc.io/vault-auto-unseal-via-aws-kms/).

- A cluster you have control over (obviously). I'm running a 5 node k3s cluster, I used [this repo](https://github.com/techno-tim/k3s-ansible) as a jumping off point to deploy it with Ansible.

- [Helm](https://helm.sh/docs/intro/install/) installed on your machine that can control your cluster.

---

## Helm Chart

Now that we have a cluster and an (optional) KMS key, we can get to deploying the Valut. I opted to use the Helm chart provided by Hashicorp, this is by far the easiest way I have come across to install apps in Kubernetes, and seems to be the industry favorite.

The fist step was to install the Helm repo and update Helm's repos

```shell
helm repo add hashicorp https://helm.releases.hashicorp.com && helm repo update
```

Now we need to create some Kubernetes secrets for our AWS KMS config. This may seem a bit confusing, as we are creating the Vault to store secrets in, but we don't have that yet, so a Kubernetes secret will work for now. 

First we need to base64 encode the secrets. I did this from WSL on my laptop, any Linux machine will do, and there is probably a way to do it on Windows and MacOS. To encode a string, use the following syntax (make sure to use the `-n` flag for echo, or it will include a newline character and really mess up your day) `echo -n <yourStringHere> | base64`
Encode each of the values in the yaml snippet shown below, and create a file like it named `secret.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  namespace: vault
  name: vault
type: Opaque
data:
  AWS_REGION: <base64 here>
  AWS_SECRET_ACCESS_KEY: <base64 here>
  AWS_ACCESS_KEY_ID: <base64 here>
  VAULT_AWSKMS_SEAL_KEY_ID: <base64 here>
```

With that out of the way, we can create our `values.yaml`. I chose to do an HA setup with raft storage, but you can use standalone if you don't want the extra overhead. You can find a good overview of what to use in your values.yaml on [Hashicorp's Website](https://developer.hashicorp.com/vault/docs/platform/k8s/helm/configuration)

```yaml
global:
  enabled: true
server:
  extraSecretEnvironmentVars:
    - envName: AWS_REGION
      secretName: vault
      secretKey: AWS_REGION
    - envName: AWS_ACCESS_KEY_ID
      secretName: vault
      secretKey: AWS_ACCESS_KEY_ID
    - envName: AWS_SECRET_ACCESS_KEY
      secretName: vault
      secretKey: AWS_SECRET_ACCESS_KEY
    - envName: VAULT_AWSKMS_SEAL_KEY_ID
      secretName: vault
      secretKey: VAULT_AWSKMS_SEAL_KEY_ID
  dev:
    enabled: false
  standalone:
    enabled: false
  ha:
    enabled: true
    config: |
      ui = true

      listener "tcp" {
        tls_disable = 1
        address = "[::]:8200"
        cluster_address = "[::]:8201"
      }
      seal "awskms" {}
      service_registration "kubernetes" {}
      storage "raft" {
        path = "/vault/data"
      }
    raft:
      enabled: true
      setNodeId: true
      config: |
        ui = true

        listener "tcp" {
          tls_disable = 1
          address = "[::]:8200"
          cluster_address = "[::]:8201"
        }
        seal "awskms" {}
        service_registration "kubernetes" {}
        storage "raft" {
          path = "/vault/data"
        }
```
Now we can install it with `helm upgrade --install vault hashicorp/vault -f values.yaml -n vault`


Once the containers are created (check with kubectl -n vault get pods), exec into the first node and init the cluster `kubectl -n vault exec -ti vault-0 -- vault operator init`

Join the second node `kubectl  -n vault exec -ti vault-1 -- vault operator raft join http://vault-0.vault-internal:8200`

And the third node `kubectl  -n vault exec -ti vault-2 -- vault operator raft join http://vault-0.vault-internal:8200`

You should now have a running 3 node Vault cluster in Kubernetes. Nice work! It still needs a TLS cert and ingress created to access the Vault. For my certs, I use CertManager, and for ingress, I use Traefik. I won't get into the weeds about how those are set up in this post, but I will leave some yaml snippets of them below. Happy Vaulting!

### Certificate
```yaml
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: mischaf-us-prod
  namespace: vault
spec:
  secretName: mischaf-us-production-tls
  issuerRef:
    name: letsencrypt-production
    kind: ClusterIssuer
  commonName: "vault.mischaf.us"
  dnsNames:
  - "vault.mischaf.us"
```

### Ingressroute
```yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: vault-gui
  namespace: vault
  annotations:
    kubernetes.io/ingress.class: traefik-external
spec:
  entryPoints:
    - websecure
  routes:
  - match: Host(`vault.mischaf.us`)
    kind: Rule
    services:
    - name: vault-active
      port: 8200
      namespace: vault
  tls:
    secretName: mischaf-us-production-tls
```
---