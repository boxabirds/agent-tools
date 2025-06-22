/**
 * Complex TypeScript sample for testing
 */

// Interfaces and type aliases
interface User {
  id: string;
  name: string;
  email: string;
  roles: Role[];
  metadata?: Record<string, unknown>;
}

type Role = 'admin' | 'user' | 'guest';

interface Repository<T> {
  find(id: string): Promise<T | null>;
  findAll(filter?: Partial<T>): Promise<T[]>;
  create(item: Omit<T, 'id'>): Promise<T>;
  update(id: string, updates: Partial<T>): Promise<T>;
  delete(id: string): Promise<boolean>;
}

// Generic class with constraints
class InMemoryRepository<T extends { id: string }> implements Repository<T> {
  private items: Map<string, T> = new Map();

  async find(id: string): Promise<T | null> {
    return this.items.get(id) || null;
  }

  async findAll(filter?: Partial<T>): Promise<T[]> {
    const items = Array.from(this.items.values());
    if (!filter) return items;
    
    return items.filter(item => 
      Object.entries(filter).every(([key, value]) => 
        item[key as keyof T] === value
      )
    );
  }

  async create(item: Omit<T, 'id'>): Promise<T> {
    const id = Math.random().toString(36).substr(2, 9);
    const newItem = { ...item, id } as T;
    this.items.set(id, newItem);
    return newItem;
  }

  async update(id: string, updates: Partial<T>): Promise<T> {
    const item = this.items.get(id);
    if (!item) throw new Error(`Item ${id} not found`);
    
    const updated = { ...item, ...updates };
    this.items.set(id, updated);
    return updated;
  }

  async delete(id: string): Promise<boolean> {
    return this.items.delete(id);
  }
}

// Decorators
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  
  descriptor.value = async function(...args: any[]) {
    console.log(`Calling ${propertyKey} with args:`, args);
    const result = await original.apply(this, args);
    console.log(`${propertyKey} returned:`, result);
    return result;
  };
  
  return descriptor;
}

function validate(schema: any) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const original = descriptor.value;
    
    descriptor.value = async function(...args: any[]) {
      // Validation logic here
      return original.apply(this, args);
    };
    
    return descriptor;
  };
}

// Service class with decorators
class UserService {
  constructor(private repository: Repository<User>) {}

  @log
  async getUser(id: string): Promise<User | null> {
    return this.repository.find(id);
  }

  @log
  @validate({ name: 'string', email: 'email' })
  async createUser(data: Omit<User, 'id'>): Promise<User> {
    return this.repository.create(data);
  }

  async getUsersByRole(role: Role): Promise<User[]> {
    return this.repository.findAll({ roles: [role] } as Partial<User>);
  }
}

// Advanced types
type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

type ReadonlyDeep<T> = {
  readonly [P in keyof T]: T[P] extends object ? ReadonlyDeep<T[P]> : T[P];
};

// Conditional types
type IsArray<T> = T extends any[] ? true : false;
type ElementType<T> = T extends (infer E)[] ? E : never;

// Mapped types with template literal types
type EventHandlers<T> = {
  [K in keyof T as `on${Capitalize<string & K>}Change`]?: (
    newValue: T[K],
    oldValue: T[K]
  ) => void;
};

// Union and intersection types
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };

function processResult<T>(result: Result<T>): T {
  if (result.success) {
    return result.data;
  } else {
    throw result.error;
  }
}

// Namespace and module augmentation
namespace Utils {
  export function debounce<T extends (...args: any[]) => any>(
    fn: T,
    delay: number
  ): (...args: Parameters<T>) => void {
    let timeoutId: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn(...args), delay);
    };
  }
  
  export function memoize<T extends (...args: any[]) => any>(fn: T): T {
    const cache = new Map();
    
    return ((...args: Parameters<T>) => {
      const key = JSON.stringify(args);
      if (cache.has(key)) {
        return cache.get(key);
      }
      
      const result = fn(...args);
      cache.set(key, result);
      return result;
    }) as T;
  }
}

// Async iterators
async function* asyncGenerator<T>(items: T[]): AsyncGenerator<T> {
  for (const item of items) {
    await new Promise(resolve => setTimeout(resolve, 100));
    yield item;
  }
}

// Type guards
function isUser(obj: any): obj is User {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'id' in obj &&
    'name' in obj &&
    'email' in obj
  );
}

// Main async function with error handling
async function main() {
  const userRepo = new InMemoryRepository<User>();
  const userService = new UserService(userRepo);
  
  try {
    // Create users
    const admin = await userService.createUser({
      name: 'Admin User',
      email: 'admin@example.com',
      roles: ['admin']
    });
    
    const regularUser = await userService.createUser({
      name: 'Regular User',
      email: 'user@example.com',
      roles: ['user']
    });
    
    // Use async iterator
    const users = [admin, regularUser];
    for await (const user of asyncGenerator(users)) {
      console.log('Processing user:', user.name);
    }
    
    // Type narrowing
    const result: Result<User> = { success: true, data: admin };
    if (result.success) {
      console.log('User created:', result.data.name);
    }
    
  } catch (error) {
    console.error('Error in main:', error);
  }
}

// Export types and run main
export { User, UserService, Repository };
export type { Role, Result };

if (require.main === module) {
  main().catch(console.error);
}