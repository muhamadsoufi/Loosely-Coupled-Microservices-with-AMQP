using System;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.HttpsPolicy;
using Microsoft.AspNetCore.SpaServices.ReactDevelopmentServer;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using TodoApp.Models;
using TodoApp.Services;

namespace TodoApp
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllersWithViews();

            // Add CORS service
            services.AddCors(options =>
            {
                options.AddDefaultPolicy(builder =>
                {
                    builder.AllowAnyOrigin()
                        .AllowAnyMethod()
                        .AllowAnyHeader();
                });
            });

            // Configure MongoDB settings from appsettings.json or environment variables
            // Environment variables take precedence over appsettings.json
            // Format: TODO_APP_MongoSettings__ConnectionString, TODO_APP_MongoSettings__DbName, etc.
            services.Configure<MongoSettings>(Configuration.GetSection(nameof(MongoSettings)));
            
            // Register MongoSettings as a singleton service for dependency injection
            services.AddSingleton<MongoSettings>(s => 
            {
                var settings = s.GetRequiredService<IOptions<MongoSettings>>().Value;
                ValidateMongoSettings(settings);
                return settings;
            });

            // Register TodoService as a singleton
            services.AddSingleton<TodoService>();

            // Register RabbitMQ TaskEventPublisher as a singleton (optional, for direct RabbitMQ integration)
            services.AddSingleton<TaskEventPublisher>(sp =>
            {
                var logger = sp.GetRequiredService<ILogger<TaskEventPublisher>>();
                var rabbitmqHost = Configuration.GetValue<string>("RabbitMQ:Host") ?? "localhost";
                var rabbitmqPort = Configuration.GetValue<int>("RabbitMQ:Port", 5672);
                var rabbitmqUser = Configuration.GetValue<string>("RabbitMQ:User") ?? "guest";
                var rabbitmqPassword = Configuration.GetValue<string>("RabbitMQ:Password") ?? "guest";
                
                return new TaskEventPublisher(logger, rabbitmqHost, rabbitmqPort, rabbitmqUser, rabbitmqPassword);
            });
        }

        /// <summary>
        /// Validates that MongoDB settings are properly configured
        /// </summary>
        private void ValidateMongoSettings(MongoSettings settings)
        {
            if (string.IsNullOrWhiteSpace(settings.ConnectionString))
                throw new InvalidOperationException("MongoDB ConnectionString is not configured. Set TODO_APP_MongoSettings__ConnectionString environment variable.");
            
            if (string.IsNullOrWhiteSpace(settings.DbName))
                throw new InvalidOperationException("MongoDB DbName is not configured. Set TODO_APP_MongoSettings__DbName environment variable.");
            
            if (string.IsNullOrWhiteSpace(settings.TodoCollection))
                throw new InvalidOperationException("MongoDB TodoCollection is not configured. Set TODO_APP_MongoSettings__TodoCollection environment variable.");
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            else
            {
                app.UseExceptionHandler("/Error");
                app.UseHsts();
            }

            // Serve static files from wwwroot (React app)
            app.UseStaticFiles();
            
            app.UseRouting();

            // Add CORS policy
            app.UseCors(builder =>
            {
                builder.AllowAnyOrigin()
                    .AllowAnyMethod()
                    .AllowAnyHeader();
            });

            app.UseEndpoints(endpoints =>
            {
                // API routes
                endpoints.MapControllerRoute(
                    name: "default",
                    pattern: "{controller}/{action=Index}/{id?}");
                
                // Fallback to index.html for SPA routing (all non-API routes)
                endpoints.MapFallbackToFile("index.html");
            });
        }
    }
}
