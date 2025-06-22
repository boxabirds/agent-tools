/**
 * Complex C++ sample for testing
 */

#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <functional>
#include <map>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <chrono>
#include <queue>
#include <optional>
#include <variant>

// Forward declarations
template<typename T> class ThreadSafeQueue;
class Task;

// Template class with SFINAE
template<typename T, typename Enable = void>
class Serializer {
public:
    static std::string serialize(const T& obj) {
        return "Generic serialization";
    }
};

// Template specialization
template<typename T>
class Serializer<T, typename std::enable_if<std::is_arithmetic<T>::value>::type> {
public:
    static std::string serialize(const T& obj) {
        return std::to_string(obj);
    }
};

// Abstract base class
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    virtual void draw() const = 0;
    
protected:
    Shape() = default;
};

// Concrete implementations
class Circle : public Shape {
private:
    double radius_;
    
public:
    explicit Circle(double radius) : radius_(radius) {}
    
    double area() const override {
        return 3.14159 * radius_ * radius_;
    }
    
    double perimeter() const override {
        return 2 * 3.14159 * radius_;
    }
    
    void draw() const override {
        std::cout << "Drawing circle with radius " << radius_ << std::endl;
    }
};

class Rectangle : public Shape {
private:
    double width_, height_;
    
public:
    Rectangle(double width, double height) 
        : width_(width), height_(height) {}
    
    double area() const override {
        return width_ * height_;
    }
    
    double perimeter() const override {
        return 2 * (width_ + height_);
    }
    
    void draw() const override {
        std::cout << "Drawing rectangle " << width_ << "x" << height_ << std::endl;
    }
};

// Thread-safe queue implementation
template<typename T>
class ThreadSafeQueue {
private:
    mutable std::mutex mutex_;
    std::condition_variable cond_;
    std::queue<T> queue_;
    
public:
    void push(T value) {
        {
            std::lock_guard<std::mutex> lock(mutex_);
            queue_.push(std::move(value));
        }
        cond_.notify_one();
    }
    
    std::optional<T> try_pop() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return std::nullopt;
        }
        T value = std::move(queue_.front());
        queue_.pop();
        return value;
    }
    
    T wait_and_pop() {
        std::unique_lock<std::mutex> lock(mutex_);
        cond_.wait(lock, [this] { return !queue_.empty(); });
        T value = std::move(queue_.front());
        queue_.pop();
        return value;
    }
    
    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }
};

// Task system with std::function
class Task {
private:
    std::function<void()> func_;
    std::string name_;
    
public:
    Task(std::function<void()> func, const std::string& name) 
        : func_(std::move(func)), name_(name) {}
    
    void execute() {
        std::cout << "Executing task: " << name_ << std::endl;
        func_();
    }
    
    const std::string& name() const { return name_; }
};

// Thread pool implementation
class ThreadPool {
private:
    std::vector<std::thread> workers_;
    ThreadSafeQueue<std::unique_ptr<Task>> tasks_;
    std::atomic<bool> stop_{false};
    
    void worker_thread() {
        while (!stop_) {
            auto task = tasks_.try_pop();
            if (task && *task) {
                (*task)->execute();
            } else {
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        }
    }
    
public:
    explicit ThreadPool(size_t num_threads) {
        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back(&ThreadPool::worker_thread, this);
        }
    }
    
    ~ThreadPool() {
        stop_ = true;
        for (auto& worker : workers_) {
            worker.join();
        }
    }
    
    void submit(std::unique_ptr<Task> task) {
        tasks_.push(std::move(task));
    }
};

// Variant and visitor pattern
using Value = std::variant<int, double, std::string>;

struct ValuePrinter {
    void operator()(int val) const {
        std::cout << "Integer: " << val << std::endl;
    }
    
    void operator()(double val) const {
        std::cout << "Double: " << val << std::endl;
    }
    
    void operator()(const std::string& val) const {
        std::cout << "String: " << val << std::endl;
    }
};

// RAII wrapper
template<typename Resource, typename Deleter>
class ResourceWrapper {
private:
    Resource* resource_;
    Deleter deleter_;
    
public:
    ResourceWrapper(Resource* res, Deleter del) 
        : resource_(res), deleter_(del) {}
    
    ~ResourceWrapper() {
        if (resource_) {
            deleter_(resource_);
        }
    }
    
    // Delete copy operations
    ResourceWrapper(const ResourceWrapper&) = delete;
    ResourceWrapper& operator=(const ResourceWrapper&) = delete;
    
    // Move operations
    ResourceWrapper(ResourceWrapper&& other) noexcept 
        : resource_(std::exchange(other.resource_, nullptr))
        , deleter_(std::move(other.deleter_)) {}
    
    ResourceWrapper& operator=(ResourceWrapper&& other) noexcept {
        if (this != &other) {
            if (resource_) {
                deleter_(resource_);
            }
            resource_ = std::exchange(other.resource_, nullptr);
            deleter_ = std::move(other.deleter_);
        }
        return *this;
    }
    
    Resource* get() const { return resource_; }
    Resource* operator->() const { return resource_; }
    Resource& operator*() const { return *resource_; }
};

// Lambda with captures
auto make_counter() {
    int count = 0;
    return [count]() mutable -> int {
        return ++count;
    };
}

// Constexpr function
constexpr int factorial(int n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}

// Main function demonstrating features
int main() {
    // Smart pointers and polymorphism
    std::vector<std::unique_ptr<Shape>> shapes;
    shapes.push_back(std::make_unique<Circle>(5.0));
    shapes.push_back(std::make_unique<Rectangle>(4.0, 6.0));
    
    for (const auto& shape : shapes) {
        shape->draw();
        std::cout << "Area: " << shape->area() 
                  << ", Perimeter: " << shape->perimeter() << std::endl;
    }
    
    // Thread pool usage
    ThreadPool pool(4);
    
    for (int i = 0; i < 10; ++i) {
        auto task = std::make_unique<Task>(
            [i]() {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                std::cout << "Task " << i << " completed" << std::endl;
            },
            "Task " + std::to_string(i)
        );
        pool.submit(std::move(task));
    }
    
    // Variant usage
    std::vector<Value> values = {42, 3.14, "Hello"};
    for (const auto& val : values) {
        std::visit(ValuePrinter{}, val);
    }
    
    // Lambda usage
    auto counter = make_counter();
    std::cout << "Counter: " << counter() << ", " << counter() << std::endl;
    
    // Compile-time computation
    constexpr int fact5 = factorial(5);
    std::cout << "Factorial of 5: " << fact5 << std::endl;
    
    // Algorithm usage
    std::vector<int> numbers = {3, 1, 4, 1, 5, 9, 2, 6};
    std::sort(numbers.begin(), numbers.end());
    
    auto it = std::find_if(numbers.begin(), numbers.end(), 
                          [](int n) { return n > 5; });
    if (it != numbers.end()) {
        std::cout << "First number > 5: " << *it << std::endl;
    }
    
    // Range-based for with structured bindings
    std::map<std::string, int> scores = {
        {"Alice", 95},
        {"Bob", 87},
        {"Charlie", 92}
    };
    
    for (const auto& [name, score] : scores) {
        std::cout << name << ": " << score << std::endl;
    }
    
    return 0;
}