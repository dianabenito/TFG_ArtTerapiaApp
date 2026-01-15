# Frontend Services

Servicios de comunicación con la API backend.

## userService
- `getUsers()`: Obtiene lista de usuarios
- `getUserById(userId)`: Obtiene usuario por ID
- `createUser(userData)`: Registra nuevo usuario
- `login(credentials)`: Login con email/password
- `getCurrentUser()`: Usuario actual autenticado
- `logout()`: Cierra sesión

## sessionsService
- `getActiveSession()`: Sesión activa del usuario
- `getNextSession()`: Próxima sesión (activa o futura)
- `endSession(sessionId)`: Finaliza sesión (terapeuta)
- `getSession(sessionId)`: Información de sesión por ID
- `getMySessions()`: Todas las sesiones del usuario
- `createSession(patientId, sessionData)`: Crea sesión (terapeuta)
- `deleteSession(sessionId)`: Elimina sesión (terapeuta)
- `updateSession(sessionId, sessionData)`: Actualiza sesión
- `getImagesForSession(sessionId)`: Imágenes de sesión

## comfyService
- `createImage(prompt, userId, sessionId)`: Genera imagen txt2img
- `convertirBoceto(prompt, userId, sessionId)`: Convierte boceto img2img
- `generateImageByMultiple(images, count, userId, sessionId)`: Combina múltiples imágenes
- `uploadImage(file, userId, isDrawnImage)`: Sube imagen al servidor
- `uploadDrawnImage(file, userId)`: Sube dibujo de canvas
- `getImagesForUser(userId)`: Todas las imágenes del usuario
- `getTemplateImages()`: Lista de imágenes plantilla
- `linkImageToSession(imageFileName, userId, sessionId)`: Asocia imagen a sesión

Ver JSDoc en archivos fuente para detalles completos de parámetros y respuestas.
