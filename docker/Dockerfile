FROM python:3.7

# set a directory for the app
WORKDIR /usr

# copy all the files to the container
#COPY /gphoto2-updater .
RUN wget --quiet https://raw.githubusercontent.com/gonzalo/gphoto2-updater/master/gphoto2-updater.sh
RUN chmod +x gphoto2-updater.sh
RUN ./gphoto2-updater.sh --stable
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y \
    qt5-default pyqt5-dev pyqt5-dev-tools \
    libcups2-dev \
    cups
#RUN apt-get -y install gphoto2 libgphoto2-dev #don't install because of gphoto2-updater file
# Set the locale
#for language german
RUN apt-get -y install locales
RUN sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG de_DE.UTF-8  
ENV LANGUAGE de_DE:en  
ENV LC_ALL de_DE.UTF-8     
# install dependencies
RUN pip install --no-cache-dir -r requirements.txt


WORKDIR /usr/src
#CMD python -m photobooth
