# Example: Archiving with Popper

Popper currently supports archiving with two of the most common services, 
**Zenodo** and **Figshare**. The following guide describes the process of 
archiving with Popper using both of these services.

### Archive on Zenodo

Follow these steps to publish an article of your research on zenodo.

**Setup an account on zenodo and obtain OAuth token**

1. Go to [zenodo.org](https://zenodo.org/) and click on *Sign Up* 
in the top right corner.
2. Sign up using an email-id or Github account or ORCID.
3. After signup, go the [*Applications*]
(https://zenodo.org/account/settings/applications/) tab from the menu.
![](https://raw.githubusercontent.com/systemslab/popper/docs-reorg/docs/figures/zenodo1.png)
4. Click on New Token on the right, in the *Personal Access Tokens* section.
![](https://raw.githubusercontent.com/systemslab/popper/docs-reorg/docs/figures/zenodo2.png)
5. Give a name to the token and give `deposit:actions` and 
`deposit:write` scopes and click on *Create*.
6. The access token is now shown. Copy this and keep it safe somewhere 
for now, as it will not be shown again.

**Work with popper**

1. **Add some metadata**: Zenodo requires some metadata to be published 
with the article, which is stored in the *.popper.yml* file.

```bash
popper metadata add --title='<Add a suitable title>'
popper metadata add --abstract='<Add a suitable description>'
popper metadata add --author1='<Name, email, affiliation>'
popper metadata add --author2='<Name, email, affiliation>'
...
popper metadata --add keywords='<Comma, Separated, Keywords>'
```

2. **Commit your changes**: This tutorial assumes all your previous
changes are committed to git.

```bash
git add .popper.yml
git commit -m "Add metadata for publishing to zenodo"
```

3. **Publish your snapshot**: Now you can publish your changes to zenodo 
with the command `popper archive --service zenodo` but there is one more 
thing, the access token! The access token can be provided using any of 
the following ways:
    1. `export POPPER_ZENODO_API_TOKEN=<Your access token>`
    2. `popper archive --service zenodo --key <Your access token>`
    3. If you don't provide your access key using the above two methods, popper will ask you for the key. After you provide it, you can answer in affirmative when popper asks to store the key. This requires you to enter a passkey, which you can use later to let popper retrieve the access token.
    ```bash
    popper archive --service zenodo
    No access token found for zenodo
    Please enter your access token for zenodo: <Your access token>
    Would you like to store this key? [y/N]: y
    Enter a strong passphrase: <Secret passphrase>
    Your key is stored in .zenodo.key
    ```

Congratulations! You have successfully published to zenodo. You get your DOI after this step, which is also stored in your .popper.yml file.

```
Snapshot has been successfully published with DOI <Your Unique Identifier> and the DOI URL <Your Unique Identifier URL>
Done..!
```