FROM php:8.3-apache

# Install dependencies
RUN apt-get update && apt-get install -y \
    libsqlite3-dev \
    && docker-php-ext-install pdo pdo_sqlite

# Enable mod_rewrite
RUN a2enmod rewrite

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Set working directory
WORKDIR /app

# Copy composer files
COPY composer.json composer.lock* ./

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader

# Copy application code
COPY . .

# Create directories
RUN mkdir -p data logs

# Set DocumentRoot to public
RUN sed -i 's|/var/www/html|/app/public|g' /etc/apache2/sites-available/000-default.conf

# Allow .htaccess
RUN echo '<Directory /app/public>\n    AllowOverride All\n</Directory>' >> /etc/apache2/sites-available/000-default.conf

# Expose port 80
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]
