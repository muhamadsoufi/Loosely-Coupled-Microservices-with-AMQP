import React from 'react';
import './todo-app.css';

const fetchItems = (baseUrl) => fetch(`${baseUrl}/todos`);

const createTodoItem = (baseUrl, todo) => fetch(`${baseUrl}/todos`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(todo)
})

const updateTodoItem = (baseUrl, todo) => fetch(`${baseUrl}/todos/${todo.id}`, {
    method: 'PUT',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(todo)
});

const deleteTodoItem = (baseUrl, id) => fetch(`${baseUrl}/todos/${id}`, {
    method: "DELETE"
})

const TodoApp = ({baseUrl}) => {
    const [list, setList] = React.useState([]); 
    const [isLoading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [filter, setFilter] = React.useState('all');
    const [editingId, setEditingId] = React.useState(null);
    const [editText, setEditText] = React.useState('');
    const inputRef = React.useRef(null);
    
    const setupData = async () => {
        try {
            const response = await fetchItems(baseUrl);
            const data = await response.json();
            setList(data);
            setError(null);
            setLoading(false);
        } catch (err) {
            setError('Failed to load tasks');
            setLoading(false);
        }
    };

    React.useEffect(() => {
        setupData()
        return () => {}
    }, [isLoading]); 
    
    const onCreateItem = async (e) => {
        e.preventDefault();
        const description = inputRef.current.value.trim();
        if (!description) {
            inputRef.current.focus();
            return;
        }
        
        setLoading(true);
        try {
            await createTodoItem(baseUrl, {description});
            inputRef.current.value = '';
            inputRef.current.focus();
            await setupData();
        } catch (err) {
            setError('Failed to add task');
            setLoading(false);
        }
    };
    
    const setTaskStatus = async (item, isCompleted) => {
        setLoading(true);
        try {
            await updateTodoItem(baseUrl, {...item, isCompleted});
            await setupData();
        } catch (err) {
            setError('Failed to update task');
            setLoading(false);
        }
    };
    
    const onRemoveItem = async (item) => {
        setLoading(true);
        try {
            await deleteTodoItem(baseUrl, item.id);
            await setupData();
        } catch (err) {
            setError('Failed to delete task');
            setLoading(false);
        }
    };

    const startEditing = (item) => {
        setEditingId(item.id);
        setEditText(item.description);
    };

    const saveEdit = async (item) => {
        const trimmed = editText.trim();
        if (!trimmed) {
            setEditingId(null);
            return;
        }
        setLoading(true);
        try {
            await updateTodoItem(baseUrl, {...item, description: trimmed});
            setEditingId(null);
            await setupData();
        } catch (err) {
            setError('Failed to edit task');
            setLoading(false);
        }
    };

    const cancelEdit = () => {
        setEditingId(null);
        setEditText('');
    };

    const clearCompleted = async () => {
        const completed = list.filter(item => item.isCompleted);
        setLoading(true);
        try {
            for (const item of completed) {
                await deleteTodoItem(baseUrl, item.id);
            }
            await setupData();
        } catch (err) {
            setError('Failed to clear completed');
            setLoading(false);
        }
    };
    
    const completedCount = list.filter(item => item.isCompleted).length;
    const activeCount = list.filter(item => !item.isCompleted).length;
    const totalCount = list.length;

    const filteredList = list.filter(item => {
        if (filter === 'active') return !item.isCompleted;
        if (filter === 'completed') return item.isCompleted;
        return true;
    });
    
    return (
        <div className='todo-app-wrapper'>
            <div className='todo-decorative-circle circle-1'></div>
            <div className='todo-decorative-circle circle-2'></div>
            <div className='todo-decorative-circle circle-3'></div>
            
            <div className='todo-app-container'>
                <div className='todo-header'>
                    <div className='header-content'>
                        <h1 className='todo-title'>✨ TaskMaster V3</h1>
                        <p className='todo-subtitle'>Organize • Track • Accomplish</p>
                    </div>
                    <div className='header-icon'>📋</div>
                </div>
                
                {error && <div className='error-message'>{error}</div>}
                
                <form className='todo-input-form' onSubmit={onCreateItem}>
                    <div className='input-wrapper'>
                        <span className='input-icon'>✏️</span>
                        <input 
                            disabled={isLoading} 
                            placeholder="Add a new task..."
                            ref={inputRef}
                            className='todo-input'
                            autoFocus
                        />
                        <button 
                            disabled={isLoading} 
                            onClick={onCreateItem}
                            className='add-button'
                            type='submit'
                        >
                            <span className='add-icon'>{isLoading ? '⏳' : '➕'}</span>
                            <span className='add-text'>Add</span>
                        </button>
                    </div>
                </form>
                
                {totalCount > 0 && (
                    <div className='todo-stats'>
                        <div className='stats-grid'>
                            <div className='stat-item'>
                                <span className='stat-number'>{totalCount}</span>
                                <span className='stat-label'>Total</span>
                            </div>
                            <div className='stat-item'>
                                <span className='stat-number'>{activeCount}</span>
                                <span className='stat-label'>Active</span>
                            </div>
                            <div className='stat-item'>
                                <span className='stat-number'>{completedCount}</span>
                                <span className='stat-label'>Done</span>
                            </div>
                            <div className='stat-item'>
                                <span className='stat-number'>{Math.round((completedCount / totalCount) * 100)}%</span>
                                <span className='stat-label'>Progress</span>
                            </div>
                        </div>
                        <div className='progress-bar'>
                            <div 
                                className='progress-fill' 
                                style={{width: `${(completedCount / totalCount) * 100}%`}}
                            ></div>
                        </div>
                    </div>
                )}
                
                {list.length === 0 ? (
                    <div className='empty-state'>
                        <div className='empty-icon'>🚀</div>
                        <h2>No tasks yet!</h2>
                        <p>Start by adding your first task above</p>
                        <div className='empty-hint'>💡 Create tasks to organize your day</div>
                    </div>
                ) : (
                    <>
                        <div className='todo-filters'>
                            <button 
                                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                                onClick={() => setFilter('all')}
                            >
                                All ({totalCount})
                            </button>
                            <button 
                                className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
                                onClick={() => setFilter('active')}
                            >
                                Active ({activeCount})
                            </button>
                            <button 
                                className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
                                onClick={() => setFilter('completed')}
                            >
                                Done ({completedCount})
                            </button>
                        </div>

                        <ul className='todo-list'>
                            {filteredList.map(item => (
                                <li className={`todo-list-item ${item.isCompleted ? 'completed' : ''}`} key={item.id}>
                                    <div className='todo-item-left'>
                                        <input
                                            type='checkbox' 
                                            checked={item.isCompleted} 
                                            onChange={(e) => setTaskStatus(item, e.target.checked)}
                                            className='todo-checkbox'
                                            disabled={isLoading}
                                        />
                                        {editingId === item.id ? (
                                            <input 
                                                type='text'
                                                value={editText}
                                                onChange={(e) => setEditText(e.target.value)}
                                                className='todo-edit-input'
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') saveEdit(item);
                                                    if (e.key === 'Escape') cancelEdit();
                                                }}
                                                autoFocus
                                            />
                                        ) : (
                                            <label 
                                                className='todo-label'
                                                onDoubleClick={() => startEditing(item)}
                                            >
                                                {item.description}
                                            </label>
                                        )}
                                    </div>
                                    <div className='todo-item-actions'>
                                        {editingId === item.id ? (
                                            <>
                                                <button 
                                                    className='action-btn save-btn'
                                                    onClick={() => saveEdit(item)}
                                                    title='Save'
                                                >
                                                    ✓
                                                </button>
                                                <button 
                                                    className='action-btn cancel-btn'
                                                    onClick={cancelEdit}
                                                    title='Cancel'
                                                >
                                                    ✕
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <button 
                                                    className='action-btn edit-btn'
                                                    onClick={() => startEditing(item)}
                                                    title='Edit (or double-click)'
                                                >
                                                    ✎
                                                </button>
                                                <button 
                                                    className='action-btn delete-btn'
                                                    onClick={() => onRemoveItem(item)}
                                                    title='Delete'
                                                    disabled={isLoading}
                                                >
                                                    🗑️
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </li>
                            ))}
                        </ul>

                        {completedCount > 0 && (
                            <div className='todo-footer'>
                                <button className='clear-btn' onClick={clearCompleted}>
                                    🧹 Clear Completed ({completedCount})
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default TodoApp;