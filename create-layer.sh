cd layer
docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.14" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.14/site-packages/; exit"