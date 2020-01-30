FROM python:3.6

RUN pip install pipenv==8.2.7

WORKDIR /usr/src/app

COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

# FIXME: add pytest to the pipenv file
RUN pip install --no-cache-dir pytest

COPY . .

CMD [ "python", "blaise_nisra_case_mover_sftp.py" ]
