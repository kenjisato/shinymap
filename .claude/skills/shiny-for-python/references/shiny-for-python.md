# Shiny for Python Best Practices Guide (2024)

When helping with Shiny for Python applications, please follow these current best practices:

## Critical Don'ts:

* NEVER use `@output` decorator - it's deprecated. Use only @render.xxx` decorators
* Don't use `ui.panel_sidebar()` or `ui.panel_main()` - they don't exist anymore
* Don't use capitalized `reactive.Calc`, `reactive.Value`, `reactive.Effect` - use lowercase versions
* Don't mix Shiny Core and Express syntax in the same app

## Correct Syntax Patterns:

### Outputs (use `@render.xxx` directly):

####  Correct

```python
@render.text
def my_output():
    return "Hello"
```

#### Wrong (deprecated)

```python
@output
@render.text  
def my_output():
    return "Hello"
```

### Sidebar layouts:
#### Correct

```python
app_ui = ui.page_sidebar(
    ui.sidebar(
        # inputs here
    ),
    # main content here
)
```

### Wrong (doesn't exist)

```python
ui.panel_sidebar()  # Don't use this
ui.panel_main()     # Don't use this
```


### Reactive functions:

#### Correct

```python
my_val = reactive.value(0)
my_calc = reactive.calc(lambda: x + 1)
my_effect = reactive.effect(lambda: print("hello"))
```

#### Wrong

```python
reactive.Value(0)  # Don't capitalize
reactive.Calc(...)  # Don't capitalize
```

## Current Import Patterns:


### Shiny Core:

```python
from shiny import App, render, ui, reactive
```


### Shiny Express:

```python
from shiny import reactive  # reactive is NOT in shiny.express
from shiny.express import input, ui, render
```


## Preferred Libraries:

* Use matplotlib instead of plotly for plots
* Use urllib3 for HTTP requests
* Avoid large packages like scipy unless necessary

## App Structure:

* End Core apps with `app = App(app_ui, server)`
* Use `app_ui = ... (static), not app_ui = function(...)`
* Put requirements in requirements.txt

Always check the official Shiny for Python documentation for the most current syntax, as it's actively evolving.



## How to Develop React Integration

To integrate a custom React library into a Shiny for Python app, you'll need to create a custom HTML dependency and use Shiny's JavaScript communication capabilities. Here's how you can achieve this:

### 1. Package Structure
First, create a Python package structure like this:

```
my_react_shiny/
├── __init__.py
├── www/
│   ├── my-react-component.js
│   ├── my-react-component.css (optional)
│   └── react.min.js (if not using CDN)
└── components.py
```

### 2. Create the HTML Dependency

In your `components.py` file, define the HTML dependency:

```python
from htmltools import HTMLDependency
from shiny import ui
from pathlib import Path

def react_dependency():
    """Create HTML dependency for React and your custom component"""
    www_dir = Path(__file__).parent / "www"
    
    return HTMLDependency(
        name="my-react-component",
        version="1.0.0",
        source={"subdir": str(www_dir)},
        script=["my-react-component.js"],
        stylesheet=["my-react-component.css"],  # optional
        # You might also need React if not already loaded
        head="""
        <script crossorigin src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
        """
    )
```

### 3. Create Python Wrapper Functions

Create wrapper functions that generate the necessary HTML and include your dependency:

```python
def my_react_component(id, **props):
    """Create a custom React component"""
    
    # Include the dependency
    dep = react_dependency()
    
    # Create a div that will host your React component
    div = ui.div(
        id=id,
        **props,
        # Add data attributes for component configuration
        **{f"data-{k}": v for k, v in props.items()}
    )
    
    # Attach the dependency
    div = div.add_deps(dep)
    
    return div

def my_react_component_output(id):
    """Create output for React component"""
    return ui.div(id=id, class_="my-react-output")
```

### 4. JavaScript Side (www/my-react-component.js)

In your JavaScript file, create the React component and set up communication with Shiny:

```javascript
// Assuming your React component is already compiled/bundled
// This is a simplified example
$(document).on('shiny:connected', function() {
  
  // Initialize React components when Shiny connects
  $('.my-react-component').each(function() {
    const element = this;
    const props = $(element).data(); // Get data attributes as props
    
    // Render your React component
    ReactDOM.render(
      React.createElement(MyCustomReactComponent, {
        ...props,
        onValueChange: function(value) {
          // Send value back to Shiny
          Shiny.setInputValue(element.id, value);
        }
      }),
      element
    );
  });
});

// Handle updates from Shiny server
Shiny.addCustomMessageHandler('update-react-component', function(message) {
  // Update your React component based on server messages
  const element = document.getElementById(message.id);
  if (element) {
    // Re-render with new props
    ReactDOM.render(
      React.createElement(MyCustomReactComponent, message.props),
      element
    );
  }
});
```

### 5. Example Usage in Shiny App

Here's how you would use your custom React component in a Shiny app:

```python
# app.py

from shiny import App, render, ui, reactive
# Import your custom component
# from my_react_shiny.components import my_react_component, my_react_component_output

# For this example, I'll mock the component
def my_react_component(id, initial_value="", placeholder="Enter text"):
    """Mock React component - replace with actual implementation"""
    from htmltools import HTMLDependency
    
    # Mock dependency
    dep = HTMLDependency(
        name="mock-react",
        version="1.0.0",
        source={"subdir": "."},
        script={"src": "https://unpkg.com/react@17/umd/react.production.min.js"},
    )
    
    div = ui.div(
        id=id,
        class_="my-react-component",
        ui.tags.script(f"""
        // Mock React component initialization
        setTimeout(function() {{
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = '{placeholder}';
            input.value = '{initial_value}';
            input.addEventListener('input', function() {{
                if (window.Shiny) {{
                    Shiny.setInputValue('{id}', this.value);
                }}
            }});
            document.getElementById('{id}').appendChild(input);
        }}, 100);
        """),
        style="border: 1px solid #ccc; padding: 10px; margin: 10px;"
    )
    
    return div.add_deps(dep)

app_ui = ui.page_fluid(
    ui.h2("Custom React Component in Shiny"),
    
    # Use your custom React component
    my_react_component(
        id="react_input",
        initial_value="Hello from React!",
        placeholder="Type something..."
    ),
    
    # Display the value from React component
    ui.h4("Value from React component:"),
    ui.output_text("react_value"),
    
    # Button to update React component from server
    ui.input_action_button("update_react", "Update React Component"),
)

def server(input, output, session):
    
    @output
    @render.text
    def react_value():
        # Access the value from your React component
        return f"Current value: {input.react_input()}"
    
    @reactive.Effect
    @reactive.event(input.update_react)
    def _():
        # Send message to update React component
        session.send_custom_message(
            "update-react-component",
            {
                "id": "react_input",
                "props": {
                    "value": f"Updated at {input.update_react()}",
                    "placeholder": "Updated from server!"
                }
            }
        )

app = App(app_ui, server)
```


### 6. Advanced Features

For more advanced integration, you can:

Handle Complex Data Types

```python
import json

def send_data_to_react(session, component_id, data):
    """Send complex data to React component"""
    session.send_custom_message("update-react-data", {
        "id": component_id,
        "data": json.dumps(data)
    })
Create Reactive React Components

from shiny import reactive

@reactive.Calc
def react_data():
    # Process data for React component
    return {"charts": [...], "filters": [...]}

@reactive.Effect
def _():
    # Update React component when data changes
    send_data_to_react(session, "my_component", react_data())
```

### 7. Distribution
To distribute your package:

Create a proper setup.py or pyproject.toml
Include the www directory in your package data
Publish to PyPI

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="my-react-shiny",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "my_react_shiny": ["www/*"],
    },
    install_requires=[
        "shiny",
        "htmltools",
    ],
)
```

This approach allows you to create reusable React components that seamlessly integrate with Shiny for Python applications, providing the rich interactivity of React with the data processing power of Python.