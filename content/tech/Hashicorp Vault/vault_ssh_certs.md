---
title: "Vault SSH Cert Management"
date: 2023-02-15T21:21:06-08:00
draft: false
---

## Background
There are quite a few ways you can authenticate over SSH, I'll outline what seem to be the most popular ones:

- Probably the most common is to just use a password, this is neither enjoyable for the user, nor is it the most secure way to do things. If you have password auth enabled on a public facing server, its going to get hammered with attempts from bots all day. You can install Fail2ban, which might stop the most unsophisticated of attacks, but attackers are smart enough to try from multiple IP addresses now. There's a project called Crowdsec that dubs itself "The spiritual successor to Fail2ban", which does this a bit more intelligently by using a crowd sourced list of bad IPs. Even with this in place though, don't use password auth. Just don't, use the next option at bare minimum.


- The next best option is to use keypairs. This consists of a private key (only you have this private key, hence the name), and a public key (this key lives in the `authorized_keys` file on the server you're trying to connect to). The private key is used to decrypt a message sent by the target server which was encrypted by the public key. The private key is the only thing that can decrypt this message, provided you're using a strong algorithm (ed25519 is what most people recommend these days). This is a whole lot better than a password, but there are still some issues. This is putting a lot of trust on the machine where the private key lives, which is presumably somebody's laptop or workstation. I've come top learn over the years of working in IT that workstations can be scary places. People use them to browse the web, and often to install sketchy shit they downloaded from the web. 

What if there was a way to leverage a trusted server to authenticate the user, rather than just blindly trusting the private key on the users machine? That's where ssh certificates come in. With certificates, rather than having a target machine trust a public key tied to a user's private key, we have that target server trust a public key signed by a CA. That certificate authority gets requests from the user to sign a certificate that leverages the keypair that lives on their machine. This is basically ssh keys on steroids. Ultimately the decision of whether or not somebody can access the target server gets moved to the CA, not the user's machine. This pattern has gained a lot of popularity in the past few years. Its fairly trivial to set up for a proof of concept, you just need a CA, and can sign certificates with some `openssl` commands. On the target machine, you just need the root CA's public key, and a simple one line modification to the sshd config file. Managing this at scale is where things tend to get tricky however. A few companies have come up with products that make this easier to manage at scale. I've tried a few of them and will give some brief opinions below.

#### Commercial Offerings

- Smallstep - Fairly simple to set up, reliable and consistent. You can set up an external IDP which will do the authentication piece. Basically just log in with Google, or whatever you use, and its that easy for users. They offer a free tier, so if you wanted to use this at home, you should have no issues. That said, its very basic and really doesn't offer the cleanest end user experience. Configuring target hosts felt a bit clunky compared to other options. This was a really solid option all things said though.

- BastionZero - Very secure and cool technology at play. They use a double root of trust, meaning if your IDP got compromised, the attacker would also need to compromise BastionZero's systems. The people behind it are brilliant, like some seriously smart people, so I'd say this may be the most secure option available. They don't offer a free tier as far as I can tell, so not a great homelab option. When we demoed this at work, it still felt a bit immature, there were a good bit of bugs we encountered with the client, and it felt a bit heavy compared to other options (this doesn't use the regular ssh binary, it uses its own proprietary one). Perhaps the biggest downfall of their architecture was that all of your traffic gets routed through the cloud, this resulted in slow performance compared to a regular ssh session.

- StrongDM - This option uses regular ssh under the hood, as SmallStep does as well. They offer a command line client, as well a a GUI client, both of which are very easy to use and user friendly. They also leverage an external IDP (including SAML and OIDC), SmallStep offers OIDC but not SAML. Configuring target hosts is very simple, just add the root CA key somewhere on the machine, and edit a single line of the ssh config. They do not offer a free tier, and the pricing isn't the cheapest thing in the world. That said, its a really solid product and by far the best choice for an enterprise in my opinion. Its very much a "set it and forget it" type of product.

- Teleport - I have never used this one, but thought it was worth mentioning. It seems a bit "heavy" based on my research, you can't just use the regular openssh client, you need to use their proprietary one. It does offer a free tier, so this may be worth checking out. I've heard good things about it.

- Hashicorp Vault - Vault offers a ssh certificate secrets engine on top of the other variety of things it does. Its probably the most basic of the options listed above, and not something I tested out at work. Vault basically provides the CA, and some fairly simple `vault` commands to request certificates, leveraging whatever method you use to authenticate to the Vault with. Its not at all fancy, and not very user friendly out of the box. That said, I already run a Vault at home, and its something a lot of companies already have. Vault has an open source offering, and in my opinion Hashicorp really does a good job of differentiating their paid and free product without coming off as greedy. The free open source Vault is great, and if you have a lot of secrets to store, you can really get a lot of value for free with it. 

With all of this in mind, I chose to use Vault for my home use. I'll be showing how I set up Vault as my ssh cert CA, as well as a script I wrote to make it a bit more user friendly.

---

### Vault Configuration
This all assumes you have a Hashicorp Vault up and running already. There are plenty of guides put there on how to do this (including one on this blog about how to set it up in Kubernetes). It's also assumed that you have the proper permissions to do all of this on your Vault.

First we need to configure the Vault's SSH signing secret engine. All of these steps are also available in Hashicorp's documentation, so if you get stuck, or something seems unclear, make sure to check there.
```shell
vault secrets enable -path=ssh-client-signer ssh
```
Note that the path here is completely up to you, this was what the example in the Vault documentation uses, and I saw no need to change it personally.

Next we need to create a CA key, you are able to use an existing one as well, but I prefer to just leave the private key in the Vault and never see it.

```shell
vault write ssh-client-signer/config/ca generate_signing_key=true
```

The last thing we need for the Vault is a signing role, modify the command below as needed, and run it to create your role. The most important thing to pay attention to is the default user, this user needs to exist on the target server.

```shell
 vault write ssh-client-signer/roles/ssh-user -<<"EOH"
{
  "algorithm_signer": "rsa-sha2-256",
  "allow_user_certificates": true,
  "allowed_users": "*",
  "allowed_extensions": "permit-pty,permit-port-forwarding",
  "default_extensions": {
    "permit-pty": ""
  },
  "key_type": "ca",
  "default_user": "yourUser",
  "ttl": "30m0s"
}
EOH
```
### Target Server Configuration
Log into one of the machines you want to use as a target, ie one you plan to ssh into with these certificates. Run the command below to write out the public key for the Vault CA we just created into the `/etc/ssh` directory. Make sure to replace the `<your vault address>` section with the actual address of your Vault (don't forget the port if not listening on port 443 or 80)
```shell
curl -o /etc/ssh/trusted-user-ca-keys.pem https://<your vault address>/v1/ssh-client-signer/public_key
```
Edit the `/etc/ssh/sshd_config` file, and add the following line to the end of it:
```shell
TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pem
```

Finally, restart sshd to load the new config `systemctl restart sshd`
### Script
Here is where the script comes in, the process of creating a key, and requesting a cert from Vault is a bit convoluted, and immediately struck me as something I wouldn't want to need to do all the time. That's why I spent a bit of time writing this script. It should handle creating the ssh keypair for you if it doesn't exist, as well as requesting the cert from Vault. It then will also save the cert to a file, make sure the permissions are correct on the cert, and add the private key to your ssh agent. The goal here was being able to ssh into the target server without much more fuss than just using a regular ssh key. This results in short lived ssh access that's tied to your Vault authentication rather than a key that sits around on your machine indefinitely.

```shell
#!/bin/bash
TYPE=ed25519
KEY=id_"$TYPE"_"$1"
if [ -z "$1" ]; then
    echo "Key name not provided. Use syntax 'cert <desired_key_name>' next time!"
    exit 1
fi
if test -f "$HOME"/.ssh/"$KEY"; then
    vault write -field signed_key ssh-client-signer/sign/my-role     public_key=@"$HOME"/.ssh/"$KEY".pub > "$HOME"/.ssh/"$KEY"-cert.pub
    chmod 600 "$HOME"/.ssh/"$KEY"-cert.pub
    ssh-add ~/.ssh/"$KEY"
else
    echo  $HOME/.ssh/$KEY
    ssh-keygen -t $TYPE -a 100 -f $HOME/.ssh/$KEY
    vault write -field signed_key ssh-client-signer/sign/my-role     public_key=@"$HOME/.ssh/$KEY.pub" > "$HOME"/.ssh/"$KEY"-cert.pub
    chmod 600 "$HOME"/.ssh/"$KEY"-cert.pub
    ssh-add ~/.ssh/"$KEY"
fi
```
So in practice, you can just run this script with a single argument, that argument being the name of your desired key. So if I wanted to use a key named "test", and had saved the script as `cert.sh` I would run the script as `cert.sh test`, which would create a few files for me:
```shell
id_ed25519_test.pub - standard pubkey
id_ed25519_test - standard private key 
id_ed25519_test-cert.pub - signed ssh certificate
```
The script will also add the private key to your ssh agent. With the naming convention it follows, the agent should be able to automatically find the signed cert, and you should be able to ssh into servers without needing to pass any additional arguments. If that doesn't work for some reason, you can simply pass the cert with the `-i` flag, ie `ssh -i ~/.ssh/id_ed25519_test-cert.pub me@myserver.com`

Finally, to make this a bit easier, you can put the script somewhere in your path, such as `/usr/local/bin/cert`. You can then simply call it with `cert <name of desired cert>`, so my workflow to ssh into a server looks like this:
1. Create the cert `cert mycert`
2. SSH into the server as you normally would, `ssh myserver`
That's it, as long as your ssh-agent is running, this should work without any additional steps. You may need to specify a user if the user on the target server differs from your local user, ie `ssh mischa@myserver`.

I hope someone finds this interesting some day, I really enjoy using this setup for all of my home ssh needs.