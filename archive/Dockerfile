FROM jupyter/scipy-notebook:latest

# Install Pandoc and LaTeX for PDF export
USER root
RUN apt-get update && apt-get install -y \
    pandoc \
    texlive-xetex \
    texlive-fonts-recommended \
    texlive-plain-generic \
    postgresql-client \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Copy and install Python requirements
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory
WORKDIR /home/jovyan