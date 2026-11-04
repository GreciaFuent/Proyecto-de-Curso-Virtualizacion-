const API_URL = "/api";

async function checkApi() {
  const status = document.getElementById("api-status");

  try {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) throw new Error("API no disponible");

    const data = await response.json();
    status.textContent = `Conectada: ${data.status}`;
    status.style.color = "green";
  } catch (error) {
    status.textContent = "No se pudo conectar con la API";
    status.style.color = "red";
  }
}

async function loadTasks() {
  const list = document.getElementById("task-list");
  list.innerHTML = "";

  try {
    const response = await fetch(`${API_URL}/tareas`);
    if (!response.ok) throw new Error("Error al cargar tareas");

    const tasks = await response.json();

    if (tasks.length === 0) {
      list.innerHTML = "<li>No hay tareas todavía.</li>";
      return;
    }

    tasks.forEach(task => {
      const item = document.createElement("li");
      item.textContent = task.nombre;
      list.appendChild(item);
    });
  } catch (error) {
    list.innerHTML = "<li>Error al cargar las tareas.</li>";
  }
}

document.getElementById("task-form").addEventListener("submit", async event => {
  event.preventDefault();

  const input = document.getElementById("task-name");
  const message = document.getElementById("form-message");
  const nombre = input.value.trim();

  if (!nombre) return;

  try {
    const response = await fetch(`${API_URL}/tareas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre })
    });

    if (!response.ok) throw new Error("No se pudo guardar");

    input.value = "";
    message.textContent = "Tarea agregada.";
    await loadTasks();
  } catch (error) {
    message.textContent = "Error al agregar la tarea.";
  }
});

checkApi();
loadTasks();
