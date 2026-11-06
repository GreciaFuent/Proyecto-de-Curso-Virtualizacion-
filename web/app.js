
const API_URL = "/api";

async function checkApi() {
  const status = document.getElementById("api-status");

  try {
    const response = await fetch(`${API_URL}/health`);

    if (!response.ok) {
      throw new Error("API no disponible");
    }

    const data = await response.json();

    status.textContent =
      `Conectada: ${data.status} | Base de datos: ${data.database || "OK"}`;

    status.style.color = "green";
  } catch (error) {
    status.textContent = "No se pudo conectar con la API";
    status.style.color = "red";
  }
}

async function loadTasks() {
  const list = document.getElementById("task-list");

  list.replaceChildren();

  try {
    const response = await fetch(`${API_URL}/tareas`);

    if (!response.ok) {
      throw new Error("Error al cargar tareas");
    }

    const tasks = await response.json();

    if (tasks.length === 0) {
      const item = document.createElement("li");
      item.textContent = "No hay tareas todavía.";
      list.appendChild(item);
      return;
    }

    tasks.forEach(task => {
      const item = document.createElement("li");

      const nombre = document.createElement("span");
      nombre.textContent = `${task.id}. ${task.nombre} `;

      const editar = document.createElement("button");
      editar.type = "button";
      editar.textContent = "Editar";

      editar.addEventListener("click", () => {
        editTask(task.id, task.nombre);
      });

      const eliminar = document.createElement("button");
      eliminar.type = "button";
      eliminar.textContent = "Eliminar";

      eliminar.addEventListener("click", () => {
        deleteTask(task.id, task.nombre);
      });

      item.appendChild(nombre);
      item.appendChild(editar);
      item.appendChild(document.createTextNode(" "));
      item.appendChild(eliminar);

      list.appendChild(item);
    });

  } catch (error) {
    const item = document.createElement("li");
    item.textContent = "Error al cargar las tareas.";
    list.appendChild(item);
  }
}

document.getElementById("task-form").addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    const input = document.getElementById("task-name");
    const message = document.getElementById("form-message");
    const nombre = input.value.trim();

    if (!nombre) return;

    try {
      const response = await fetch(`${API_URL}/tareas`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ nombre })
      });

      if (!response.ok) {
        throw new Error("No se pudo guardar");
      }

      input.value = "";
      message.textContent = "Tarea agregada correctamente.";

      await loadTasks();

    } catch (error) {
      message.textContent = "Error al agregar la tarea.";
    }
  }
);

async function editTask(id, nombreActual) {
  const nuevoNombre = prompt(
    "Editar nombre de la tarea:",
    nombreActual
  );

  if (nuevoNombre === null) return;

  const nombre = nuevoNombre.trim();

  if (!nombre) {
    alert("El nombre no puede estar vacío.");
    return;
  }

  try {
    const response = await fetch(`${API_URL}/tareas/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ nombre })
    });

    if (!response.ok) {
      throw new Error("No se pudo actualizar");
    }

    await loadTasks();

  } catch (error) {
    alert("Error al editar la tarea.");
  }
}

async function deleteTask(id, nombre) {
  const confirmado = confirm(
    `¿Seguro que deseas eliminar la tarea "${nombre}"?`
  );

  if (!confirmado) return;

  try {
    const response = await fetch(`${API_URL}/tareas/${id}`, {
      method: "DELETE"
    });

    if (!response.ok) {
      throw new Error("No se pudo eliminar");
    }

    await loadTasks();

  } catch (error) {
    alert("Error al eliminar la tarea.");
  }
}

checkApi();
loadTasks();
