// Complex Go sample for testing
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"sync"
	"time"
)

// Interfaces
type Storage interface {
	Get(ctx context.Context, key string) (interface{}, error)
	Set(ctx context.Context, key string, value interface{}) error
	Delete(ctx context.Context, key string) error
}

type Cache interface {
	Storage
	Clear(ctx context.Context) error
	Size() int
}

// Struct with embedded interface
type User struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// Generic-like implementation using interface{}
type InMemoryCache struct {
	mu    sync.RWMutex
	items map[string]interface{}
}

func NewInMemoryCache() *InMemoryCache {
	return &InMemoryCache{
		items: make(map[string]interface{}),
	}
}

func (c *InMemoryCache) Get(ctx context.Context, key string) (interface{}, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
		if val, ok := c.items[key]; ok {
			return val, nil
		}
		return nil, errors.New("key not found")
	}
}

func (c *InMemoryCache) Set(ctx context.Context, key string, value interface{}) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
		c.items[key] = value
		return nil
	}
}

func (c *InMemoryCache) Delete(ctx context.Context, key string) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	delete(c.items, key)
	return nil
}

func (c *InMemoryCache) Clear(ctx context.Context) error {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	c.items = make(map[string]interface{})
	return nil
}

func (c *InMemoryCache) Size() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	return len(c.items)
}

// Worker pool pattern
type Task struct {
	ID   int
	Data interface{}
}

type Result struct {
	TaskID int
	Output interface{}
	Error  error
}

type WorkerPool struct {
	workers   int
	taskQueue chan Task
	results   chan Result
	wg        sync.WaitGroup
}

func NewWorkerPool(workers int) *WorkerPool {
	return &WorkerPool{
		workers:   workers,
		taskQueue: make(chan Task, workers*2),
		results:   make(chan Result, workers*2),
	}
}

func (p *WorkerPool) Start(ctx context.Context, handler func(Task) (interface{}, error)) {
	for i := 0; i < p.workers; i++ {
		p.wg.Add(1)
		go p.worker(ctx, handler)
	}
}

func (p *WorkerPool) worker(ctx context.Context, handler func(Task) (interface{}, error)) {
	defer p.wg.Done()
	
	for {
		select {
		case <-ctx.Done():
			return
		case task, ok := <-p.taskQueue:
			if !ok {
				return
			}
			
			output, err := handler(task)
			p.results <- Result{
				TaskID: task.ID,
				Output: output,
				Error:  err,
			}
		}
	}
}

func (p *WorkerPool) Submit(task Task) {
	p.taskQueue <- task
}

func (p *WorkerPool) Results() <-chan Result {
	return p.results
}

func (p *WorkerPool) Stop() {
	close(p.taskQueue)
	p.wg.Wait()
	close(p.results)
}

// Error handling with custom error types
type ValidationError struct {
	Field   string
	Message string
}

func (e ValidationError) Error() string {
	return fmt.Sprintf("validation error on field %s: %s", e.Field, e.Message)
}

// Service with methods
type UserService struct {
	cache Cache
	mu    sync.Mutex
}

func NewUserService(cache Cache) *UserService {
	return &UserService{
		cache: cache,
	}
}

func (s *UserService) CreateUser(ctx context.Context, user *User) error {
	if user.Name == "" {
		return ValidationError{Field: "name", Message: "name is required"}
	}
	
	if user.Email == "" {
		return ValidationError{Field: "email", Message: "email is required"}
	}
	
	user.ID = generateID()
	user.CreatedAt = time.Now()
	user.UpdatedAt = user.CreatedAt
	
	return s.cache.Set(ctx, user.ID, user)
}

func (s *UserService) GetUser(ctx context.Context, id string) (*User, error) {
	val, err := s.cache.Get(ctx, id)
	if err != nil {
		return nil, err
	}
	
	user, ok := val.(*User)
	if !ok {
		return nil, errors.New("invalid user data")
	}
	
	return user, nil
}

// Channel patterns
func pipeline(ctx context.Context, input <-chan int) <-chan int {
	output := make(chan int)
	
	go func() {
		defer close(output)
		
		for {
			select {
			case <-ctx.Done():
				return
			case val, ok := <-input:
				if !ok {
					return
				}
				
				// Process value
				result := val * val
				
				select {
				case <-ctx.Done():
					return
				case output <- result:
				}
			}
		}
	}()
	
	return output
}

// Defer and panic/recover
func safeOperation(fn func() error) (err error) {
	defer func() {
		if r := recover(); r != nil {
			err = fmt.Errorf("panic recovered: %v", r)
		}
	}()
	
	return fn()
}

// Helper functions
func generateID() string {
	return fmt.Sprintf("%d", time.Now().UnixNano())
}

// Main function demonstrating usage
func main() {
	ctx := context.Background()
	
	// Create cache and service
	cache := NewInMemoryCache()
	userService := NewUserService(cache)
	
	// Create users
	user1 := &User{
		Name:  "John Doe",
		Email: "john@example.com",
	}
	
	if err := userService.CreateUser(ctx, user1); err != nil {
		fmt.Printf("Error creating user: %v\n", err)
	}
	
	// Worker pool example
	pool := NewWorkerPool(3)
	pool.Start(ctx, func(task Task) (interface{}, error) {
		// Simulate work
		time.Sleep(100 * time.Millisecond)
		return fmt.Sprintf("Processed task %d", task.ID), nil
	})
	
	// Submit tasks
	for i := 0; i < 10; i++ {
		pool.Submit(Task{ID: i, Data: fmt.Sprintf("data-%d", i)})
	}
	
	// Collect results
	go func() {
		for result := range pool.Results() {
			if result.Error != nil {
				fmt.Printf("Task %d failed: %v\n", result.TaskID, result.Error)
			} else {
				fmt.Printf("Task %d completed: %v\n", result.TaskID, result.Output)
			}
		}
	}()
	
	// Channel pipeline
	numbers := make(chan int)
	squared := pipeline(ctx, numbers)
	
	go func() {
		for i := 1; i <= 5; i++ {
			numbers <- i
		}
		close(numbers)
	}()
	
	for val := range squared {
		fmt.Printf("Squared: %d\n", val)
	}
	
	// Clean up
	pool.Stop()
	
	fmt.Println("Program completed")
}