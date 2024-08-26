# aws-ahi

Exploring AWS AHI with a small proxy.

```
pip install -r requirements.txt

# edit the .env file with the proper information
cp template.env .env

# Run the server. Defaults to localhost:8000
fastapi dev ./src/aws_ahi/hello.py
```

## HTTP endpoints

```js
/**
 * [
 *    {
 *      imageSetId: string,
 *      PatientId: string | null,
 *      PatientName: string | null,
 *      PatientSex: string | null,
 *      PatientBirthDate: string | null,
 *      StudyDate: string | null,
 *      StudyDescription: string | null,
 *      StudyId: string | null,
 *      StudyInstanceUID: string,
 *    },
 *    ...
 * ]
 */
fetch('http://localhost:8000/list-image-sets')

/**
 * { <image set metadata containing Patient/Study/Series/Instances/Frame info> }
 */
fetch(`http://localhost:8000/image-set/${imageSetId}`)


/**
 * Returns a binary response with mimetype application/octet-stream
 * containing the HTJ2K image.
 */
fetch(`http://localhost:8000/image-set/${imageSetId}/${frame_id}/pixel-data`)
```

## HTTP/2 setup

Make certificate

```
sudo apt-get install openssl
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

```
pip install hypercorn
hypercorn src.aws_ahi.hello:app --bind 0.0.0.0:8000 --certfile ./cert.pem --keyfile ./key.pem
```

Start chrome without security

```
google-chrome --disable-web-security --user-data-dir="/somewhere" --ignore-certificate-errors
```
