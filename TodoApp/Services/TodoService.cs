using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using MongoDB.Driver;
using Microsoft.Extensions.Logging;
using TodoApp.Models;

namespace TodoApp.Services
{
  public class TodoService
  {
    private IMongoCollection<TodoItem> _todosCollection;
    private readonly ILogger<TodoService> _logger;
    private readonly TaskEventPublisher _eventPublisher;

    public TodoService(MongoSettings settings, ILogger<TodoService> logger, TaskEventPublisher eventPublisher)
    {
      _todosCollection = new MongoClient(settings.ConnectionString)
              .GetDatabase(settings.DbName)
              .GetCollection<TodoItem>(settings.TodoCollection);
      _logger = logger;
      _eventPublisher = eventPublisher;
    }

    public IEnumerable<TodoItem> GetAll()
    {
      return _todosCollection.Find(t => true).ToList();
    }

    public TodoItem GetById(string id)
    {
      return _todosCollection.Find(t => t.Id == id).First();
    }

    public TodoItem UpdateItem(TodoItem data)
    {
      _todosCollection.ReplaceOne(t => t.Id == data.Id, data);
      
      // Publish event via RabbitMQ
      _eventPublisher.PublishTaskUpdatedAsync(data.Id, data.Description, data.IsCompleted).Wait();
      
      return data;
    }

    public TodoItem CreateItem(TodoItem data)
    {
      _todosCollection.InsertOne(data);
      
      // Publish event via RabbitMQ
      _eventPublisher.PublishTaskCreatedAsync(data.Id, data.Description).Wait();
      
      return data;
    }

    public void Delete(TodoItem item)
    {
      _todosCollection.DeleteOne(t => t.Id == item.Id);
      
      // Publish event via RabbitMQ
      _eventPublisher.PublishTaskDeletedAsync(item.Id, item.Description).Wait();
    }
  }
}
