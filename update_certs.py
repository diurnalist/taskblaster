#!/usr/bin/env python
import certifi
import shutil
import os

certfile = certifi.where()

shutil.copyfile(certfile, f"{certfile}.bak")

with open(certfile, "a") as outfile:
    outfile.write("\n# BEGIN EXTRA CERTS")
    for (dirpath, _, certs) in os.walk("certs"):
        for cert in certs:
            hostname = cert.replace(".pem", "")
            outfile.write(f"\n# {hostname}\n")
            with open(os.path.join(dirpath, cert), "r") as infile:
                outfile.write(infile.read())
