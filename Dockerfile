FROM python:3.10-slim

# Install system dependencies for the PDF generator and Arabic fonts
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    fonts-hosny-amiri \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your website files
COPY . .

# Run the website
CMD ["python", "app.py"]
