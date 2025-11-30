# ============================================
# Multi-stage build for Todo App
# Fixed Dockerfile for .NET 3.1 project
# ============================================

# Stage 1: Build React app
FROM node:14-alpine AS frontend-build
WORKDIR /app/ClientApp

COPY ClientApp/package*.json ./
RUN npm ci

COPY ClientApp ./
RUN npm run build

# Stage 2: Build and compile .NET
FROM mcr.microsoft.com/dotnet/sdk:3.1-focal AS build
WORKDIR /app

# Copy project files
COPY *.csproj ./
RUN dotnet restore

# Copy source code
COPY . .

# Copy pre-built React app to wwwroot
COPY --from=frontend-build /app/ClientApp/build ./wwwroot

# Build and publish
RUN dotnet publish -c Release -o /dist --no-restore

# Stage 3: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:3.1-focal

WORKDIR /app

# Copy application from build stage
COPY --from=build /dist .

# Create non-root user and set permissions
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Environment variables
ENV ASPNETCORE_URLS=http://+:5000
ENV ASPNETCORE_ENVIRONMENT=Production

# Run application
ENTRYPOINT ["dotnet", "TodoApp.dll"]