/**
 * Complex JavaScript sample for testing
 */

// ES6 Classes and inheritance
class EventEmitter {
  constructor() {
    this.events = new Map();
  }

  on(event, handler) {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }
    this.events.get(event).push(handler);
  }

  emit(event, ...args) {
    const handlers = this.events.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(...args));
    }
  }
}

class CustomElement extends EventEmitter {
  constructor(tagName, options = {}) {
    super();
    this.tagName = tagName;
    this.options = options;
    this.children = [];
  }

  appendChild(child) {
    this.children.push(child);
    this.emit('child-added', child);
  }

  render() {
    return `<${this.tagName}>${this.children.map(c => c.render()).join('')}</${this.tagName}>`;
  }
}

// Async/await and Promises
async function fetchUserData(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}

// Generator function
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

// Arrow functions and array methods
const processData = (items) => {
  return items
    .filter(item => item.active)
    .map(item => ({
      ...item,
      processed: true,
      timestamp: Date.now()
    }))
    .reduce((acc, item) => {
      const key = item.category || 'uncategorized';
      if (!acc[key]) acc[key] = [];
      acc[key].push(item);
      return acc;
    }, {});
};

// Destructuring and spread operator
const mergeConfig = (defaults, ...configs) => {
  const { debug = false, ...restDefaults } = defaults;
  
  return configs.reduce((merged, config) => {
    const { overrides, ...rest } = config;
    return {
      ...merged,
      ...rest,
      ...(overrides && { overrides: { ...merged.overrides, ...overrides } })
    };
  }, { debug, ...restDefaults });
};

// Template literals and tagged templates
const sql = (strings, ...values) => {
  return strings.reduce((query, str, i) => {
    return query + str + (values[i] ? `$${i + 1}` : '');
  }, '');
};

const query = sql`SELECT * FROM users WHERE age > ${18} AND city = ${'NYC'}`;

// Closure and factory pattern
const createCounter = (initialValue = 0) => {
  let count = initialValue;
  
  return {
    increment: () => ++count,
    decrement: () => --count,
    getValue: () => count,
    reset: () => { count = initialValue; }
  };
};

// Module pattern with private methods
const UserService = (() => {
  const users = new Map();
  
  // Private method
  const validateUser = (user) => {
    if (!user.id || !user.name) {
      throw new Error('Invalid user');
    }
  };
  
  // Public API
  return {
    addUser(user) {
      validateUser(user);
      users.set(user.id, user);
    },
    
    getUser(id) {
      return users.get(id);
    },
    
    getAllUsers() {
      return Array.from(users.values());
    }
  };
})();

// Complex object with getters/setters
const config = {
  _values: new Map(),
  
  get(key) {
    return this._values.get(key);
  },
  
  set(key, value) {
    this._values.set(key, value);
    this.emit?.('change', { key, value });
  },
  
  get size() {
    return this._values.size;
  }
};

// Switch statement with complex cases
function processAction(action) {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true };
    
    case 'FETCH_SUCCESS':
      return {
        ...state,
        loading: false,
        data: action.payload,
        error: null
      };
    
    case 'FETCH_ERROR':
      return {
        ...state,
        loading: false,
        error: action.error
      };
    
    default:
      return state;
  }
}

// Main execution
(async function main() {
  const counter = createCounter(10);
  console.log(counter.getValue()); // 10
  counter.increment();
  console.log(counter.getValue()); // 11
  
  const fib = fibonacci();
  for (let i = 0; i < 10; i++) {
    console.log(fib.next().value);
  }
  
  try {
    const user = await fetchUserData(123);
    UserService.addUser(user);
  } catch (error) {
    console.error('Failed to process user');
  }
})();