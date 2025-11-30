using System;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using RabbitMQ.Client;
using Microsoft.Extensions.Logging;

namespace TodoApp.Services
{
    public class TaskEventPublisher
    {
        private readonly IConnection _connection;
        private readonly IModel _channel;
        private readonly ILogger<TaskEventPublisher> _logger;
        private const string EXCHANGE_NAME = "task_events";
        
        public TaskEventPublisher(ILogger<TaskEventPublisher> logger, string rabbitmqHost, int rabbitmqPort, string rabbitmqUser, string rabbitmqPassword)
        {
            _logger = logger;
            
            try
            {
                var factory = new ConnectionFactory
                {
                    HostName = rabbitmqHost,
                    Port = rabbitmqPort,
                    UserName = rabbitmqUser,
                    Password = rabbitmqPassword,
                    AutomaticRecoveryEnabled = true,
                    NetworkRecoveryInterval = TimeSpan.FromSeconds(10),
                    RequestedHeartbeat = TimeSpan.FromSeconds(60),
                    RequestedConnectionTimeout = TimeSpan.FromSeconds(30)
                };
                
                _connection = factory.CreateConnection();
                _channel = _connection.CreateModel();
                
                // Declare exchange
                _channel.ExchangeDeclare(
                    exchange: EXCHANGE_NAME,
                    type: ExchangeType.Topic,
                    durable: true,
                    autoDelete: false
                );
                
                _logger.LogInformation("✓ RabbitMQ connection established");
            }
            catch (Exception ex)
            {
                _logger.LogError($"✗ Failed to connect to RabbitMQ: {ex.Message}");
                throw;
            }
        }
        
        public Task PublishTaskCreatedAsync(string taskId, string description)
        {
            return PublishEventAsync("task.created", taskId, description, false);
        }
        
        public Task PublishTaskUpdatedAsync(string taskId, string description, bool isCompleted)
        {
            var eventType = isCompleted ? "task.completed" : "task.updated";
            return PublishEventAsync(eventType, taskId, description, isCompleted);
        }
        
        public Task PublishTaskDeletedAsync(string taskId, string description)
        {
            return PublishEventAsync("task.deleted", taskId, description, false);
        }
        
        private Task PublishEventAsync(string eventType, string taskId, string description, bool isCompleted)
        {
            try
            {
                var taskEvent = new
                {
                    event_type = eventType,
                    task_id = taskId,
                    description = description,
                    is_completed = isCompleted,
                    timestamp = DateTime.UtcNow.ToString("O")
                };
                
                var json = JsonSerializer.Serialize(taskEvent);
                var body = Encoding.UTF8.GetBytes(json);
                
                var properties = _channel.CreateBasicProperties();
                properties.Persistent = true;
                properties.ContentType = "application/json";
                
                var routingKey = $"task.{eventType.Split('.')[1]}";
                
                _channel.BasicPublish(
                    exchange: EXCHANGE_NAME,
                    routingKey: routingKey,
                    basicProperties: properties,
                    body: body
                );
                
                _logger.LogInformation($"✓ Published event: {eventType} for task {taskId}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"✗ Failed to publish event: {ex.Message}");
            }
            
            return Task.CompletedTask;
        }
        
        public void Dispose()
        {
            _channel?.Dispose();
            _connection?.Dispose();
        }
    }
}
