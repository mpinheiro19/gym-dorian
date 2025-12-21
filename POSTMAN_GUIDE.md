# Postman Collection - Gym Dorian Bulk Insert Workout

## 📦 Importar a Collection

1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo `bulk_insert_workout.postman_collection.json`
4. A collection "Gym Dorian - Bulk Insert Workout" será importada

## 🔧 Configuração Inicial

### Variáveis da Collection

A collection já vem com as seguintes variáveis configuradas:

| Variável | Valor Padrão | Descrição |
|----------|--------------|-----------|
| `base_url` | `http://localhost:8000` | URL base da API |
| `user_email` | `user@example.com` | Email do usuário |
| `user_password` | `SecurePassword123!` | Senha do usuário |
| `access_token` | (vazio) | Token JWT (preenchido automaticamente no login) |
| `last_workout_id` | (vazio) | ID do último workout criado |
| `last_exercise_id` | (vazio) | ID do último exercício criado |

### Atualizar Variáveis (se necessário)

1. Clique com o botão direito na collection
2. Selecione **Edit**
3. Vá para a aba **Variables**
4. Atualize os valores conforme sua configuração

## 🚀 Fluxo de Uso

### 1. Autenticação

#### Primeiro Uso - Registrar Usuário

```
POST /api/auth/register
```

Execute o request **"Register User"** para criar uma nova conta.

**Importante:** Execute apenas uma vez. Se o email já existir, você receberá um erro.

#### Login

```
POST /api/auth/login
```

Execute o request **"Login"** para obter o token de autenticação.

✅ O token será **automaticamente salvo** na variável `access_token` e usado em todas as requisições subsequentes.

### 2. Criar Exercícios (Preparação)

Antes de criar workouts, você precisa ter exercícios cadastrados no sistema.

#### Listar Exercícios Existentes

```
GET /api/workouts/exercises
```

Execute **"List Exercises"** para ver os exercícios disponíveis e seus IDs.

#### Criar Novo Exercício

```
POST /api/workouts/exercises
```

Execute **"Create Exercise"** para adicionar novos exercícios.

Exemplo:
```json
{
  "name": "Bench Press",
  "muscle_group": "Chest",
  "equipment_type": "Barbell"
}
```

✅ O ID do exercício criado será **automaticamente salvo** na variável `last_exercise_id`.

### 3. Bulk Insert - Criar Workout Session Completo

```
POST /api/workouts/sessions
```

Execute **"Bulk Insert - Complete Workout Session"** para criar uma sessão completa de treino.

#### Estrutura do Request

```json
{
  "workout_date": "2025-12-17",
  "duration_minutes": 90,
  "notes": "Chest and triceps day - feeling strong!",
  "exercises": [
    {
      "exercise_id": 1,
      "sets": [
        {
          "set_number": 1,
          "reps": 10,
          "weight": 100.0,
          "rpe": 7,
          "notes": "Warm-up set",
          "rest_time_seconds": 120
        },
        {
          "set_number": 2,
          "reps": 8,
          "weight": 110.0,
          "rpe": 8,
          "rest_time_seconds": 150
        }
      ]
    },
    {
      "exercise_id": 2,
      "sets": [
        {
          "set_number": 1,
          "reps": 12,
          "weight": 40.0,
          "rpe": 6,
          "rest_time_seconds": 90
        }
      ]
    }
  ]
}
```

#### Parâmetros Detalhados

**Workout Session (nível superior):**
- `workout_date`: Data do treino (formato: YYYY-MM-DD)
- `duration_minutes`: Duração total em minutos (opcional)
- `notes`: Anotações sobre o treino (opcional)

**Exercises (array):**
- `exercise_id`: ID do exercício (obter de "List Exercises")
- `sets`: Array de séries realizadas

**Sets (array):**
- `set_number`: Número da série (1, 2, 3, ...)
- `reps`: Número de repetições (1-1000)
- `weight`: Peso utilizado em kg (0-10000)
- `rpe`: Rate of Perceived Exertion - Escala de esforço 1-10 (opcional)
- `notes`: Anotações sobre a série (opcional)
- `rest_time_seconds`: Tempo de descanso após a série em segundos (opcional)

#### Resposta do Sistema

A API retorna o workout criado com **métricas calculadas automaticamente**:

```json
{
  "id": 1,
  "user_id": 1,
  "workout_date": "2025-12-17",
  "duration_minutes": 90,
  "notes": "Chest and triceps day - feeling strong!",
  "exercises_done": [
    {
      "id": 1,
      "session_id": 1,
      "exercise": {
        "id": 1,
        "name": "Bench Press",
        "muscle_group": "Chest"
      },
      "sets": [...],
      "sets_completed": 4,      // ✅ Calculado automaticamente
      "top_weight": 120.0,      // ✅ Calculado automaticamente
      "total_reps": 32,         // ✅ Calculado automaticamente
      "total_volume": 3520.0    // ✅ Calculado automaticamente (reps * weight)
    }
  ]
}
```

✅ O ID do workout criado será **automaticamente salvo** na variável `last_workout_id`.

### 4. Consultar Workouts

#### Listar Todos os Seus Workouts

```
GET /api/workouts/sessions
```

Execute **"List My Workout Sessions"** para ver todos os seus treinos.

**Filtros disponíveis:**
- `start_date`: Data inicial (YYYY-MM-DD)
- `end_date`: Data final (YYYY-MM-DD)
- `limit`: Número máximo de resultados (padrão: 100)

#### Ver Detalhes de um Workout Específico

```
GET /api/workouts/sessions/{workout_id}
```

Execute **"Get Workout Session by ID"** usando a variável `{{last_workout_id}}`.

### 5. Atualizar Workout

#### Atualizar Metadados da Sessão

```
PUT /api/workouts/sessions/{workout_id}
```

Execute **"Update Workout Session"** para atualizar data, duração ou notas.

```json
{
  "duration_minutes": 95,
  "notes": "Updated notes"
}
```

#### Adicionar Exercício a um Workout Existente

```
POST /api/workouts/sessions/{workout_id}/exercises
```

Execute **"Add Exercise to Existing Session"** para adicionar mais um exercício.

```json
{
  "exercise_id": 4,
  "sets": [
    {
      "set_number": 1,
      "reps": 12,
      "weight": 30.0
    }
  ]
}
```

### 6. Deletar Workout

```
DELETE /api/workouts/sessions/{workout_id}
```

Execute **"Delete Workout Session"** para remover um treino completo.

⚠️ **Atenção:** Isso remove o workout e TODOS os exercícios e séries associados (CASCADE).

### 7. Estatísticas

```
GET /api/workouts/stats
```

Execute **"Get Workout Stats"** para ver estatísticas agregadas dos seus treinos.

**Filtros disponíveis:**
- `start_date`: Data inicial para cálculo das estatísticas
- `end_date`: Data final para cálculo das estatísticas

## 💡 Dicas de Uso

### 1. Workflow Recomendado

```
1. Login (uma vez)
   ↓
2. List Exercises (para pegar os IDs)
   ↓
3. Bulk Insert - Complete Workout Session (quantas vezes quiser)
   ↓
4. List My Workout Sessions (para ver os treinos criados)
```

### 2. Cenários de Uso Comuns

#### Cenário 1: Treino de Peito e Tríceps

```json
{
  "workout_date": "2025-12-17",
  "duration_minutes": 90,
  "exercises": [
    {
      "exercise_id": 1,  // Bench Press
      "sets": [
        {"set_number": 1, "reps": 10, "weight": 100.0, "rpe": 7},
        {"set_number": 2, "reps": 8, "weight": 110.0, "rpe": 8},
        {"set_number": 3, "reps": 6, "weight": 120.0, "rpe": 9}
      ]
    },
    {
      "exercise_id": 5,  // Tricep Pushdown
      "sets": [
        {"set_number": 1, "reps": 15, "weight": 20.0, "rpe": 7},
        {"set_number": 2, "reps": 12, "weight": 22.5, "rpe": 8},
        {"set_number": 3, "reps": 10, "weight": 25.0, "rpe": 9}
      ]
    }
  ]
}
```

#### Cenário 2: Treino de Pernas com Dropsets

```json
{
  "workout_date": "2025-12-18",
  "duration_minutes": 120,
  "notes": "Leg day with progressive overload",
  "exercises": [
    {
      "exercise_id": 10,  // Squat
      "sets": [
        {"set_number": 1, "reps": 12, "weight": 100.0, "rpe": 6, "rest_time_seconds": 180},
        {"set_number": 2, "reps": 10, "weight": 120.0, "rpe": 7, "rest_time_seconds": 180},
        {"set_number": 3, "reps": 8, "weight": 140.0, "rpe": 9, "rest_time_seconds": 240},
        {"set_number": 4, "reps": 12, "weight": 100.0, "rpe": 8, "notes": "Drop set", "rest_time_seconds": 120}
      ]
    }
  ]
}
```

### 3. Identificação do Usuário

🔐 **Autenticação Automática:** O usuário é identificado automaticamente através do token JWT que foi salvo no login.

- Você **NÃO precisa** passar `user_id` no body
- O sistema extrai o `user_id` do token automaticamente
- Cada usuário vê apenas seus próprios workouts

### 4. Validações do Sistema

O sistema valida automaticamente:

✅ **Set Detail:**
- `set_number`: 1-100
- `reps`: 1-1000
- `weight`: 0-10000 kg
- `rpe`: 1-10 (se fornecido)
- `rest_time_seconds`: 0-3600 (se fornecido)

✅ **Session:**
- `duration_minutes`: 1-600 minutos
- `exercises`: Mínimo 1 exercício
- Todos os `exercise_id` devem existir no banco

### 5. Testes Automáticos

A collection inclui testes automáticos que:

✅ Verificam status codes (200, 201, etc.)
✅ Validam estrutura das respostas
✅ Salvam variáveis automaticamente (token, IDs)

Os testes aparecem na aba **Test Results** após cada request.

## 🔍 Troubleshooting

### Erro 401 Unauthorized

**Problema:** Token expirado ou não fornecido.

**Solução:** Execute o request **"Login"** novamente.

### Erro 404 Exercise not found

**Problema:** O `exercise_id` fornecido não existe.

**Solução:** Execute **"List Exercises"** e use um ID válido.

### Erro 400 Bad Request

**Problema:** Dados inválidos no request body.

**Solução:** Verifique se:
- Todos os campos obrigatórios estão presentes
- Os valores estão dentro dos limites permitidos
- O formato do JSON está correto

### Variável {{access_token}} vazia

**Problema:** O token não foi salvo automaticamente.

**Solução:**
1. Execute **"Login"** novamente
2. Verifique a aba **Tests** do request de login
3. Manualmente copie o token da resposta para a variável se necessário

## 📊 Exemplo Completo - Do Zero ao Workout

### Passo 1: Registrar e Fazer Login

```bash
# 1. Register (apenas uma vez)
POST /api/auth/register
Body: {"email": "user@example.com", "password": "SecurePassword123!", "full_name": "John Doe"}

# 2. Login
POST /api/auth/login
Form: username=user@example.com, password=SecurePassword123!
# Token é salvo automaticamente
```

### Passo 2: Criar Exercícios

```bash
# 3. Create Exercise - Bench Press
POST /api/workouts/exercises
Body: {"name": "Bench Press", "muscle_group": "Chest", "equipment_type": "Barbell"}
# Response: {"id": 1, ...}

# 4. Create Exercise - Squat
POST /api/workouts/exercises
Body: {"name": "Squat", "muscle_group": "Legs", "equipment_type": "Barbell"}
# Response: {"id": 2, ...}

# 5. Create Exercise - Tricep Pushdown
POST /api/workouts/exercises
Body: {"name": "Tricep Pushdown", "muscle_group": "Triceps", "equipment_type": "Cable"}
# Response: {"id": 3, ...}
```

### Passo 3: Criar Workout Completo

```bash
# 6. Bulk Insert - Complete Workout
POST /api/workouts/sessions
Body: {
  "workout_date": "2025-12-17",
  "duration_minutes": 90,
  "notes": "Great workout!",
  "exercises": [
    {
      "exercise_id": 1,
      "sets": [
        {"set_number": 1, "reps": 10, "weight": 100.0, "rpe": 7},
        {"set_number": 2, "reps": 8, "weight": 110.0, "rpe": 8},
        {"set_number": 3, "reps": 6, "weight": 120.0, "rpe": 9}
      ]
    },
    {
      "exercise_id": 3,
      "sets": [
        {"set_number": 1, "reps": 15, "weight": 20.0, "rpe": 7},
        {"set_number": 2, "reps": 12, "weight": 22.5, "rpe": 8}
      ]
    }
  ]
}
```

### Passo 4: Verificar Resultado

```bash
# 7. List My Workouts
GET /api/workouts/sessions

# 8. Get Workout Details
GET /api/workouts/sessions/{last_workout_id}

# 9. Get Stats
GET /api/workouts/stats
```

## 🎯 Recursos Adicionais

### Variáveis de Ambiente vs Collection

A collection usa **variáveis de collection** (escopo local). Se quiser usar as mesmas variáveis em múltiplas collections:

1. Crie um **Environment** no Postman
2. Copie as variáveis da collection para o environment
3. Selecione o environment antes de executar os requests

### Exportar Dados

Você pode exportar os responses salvando-os como **Examples** nos requests:

1. Execute o request
2. Clique em **Save Response**
3. Nomeie o example
4. Use como referência ou documentação

## 📝 Notas

- ✅ Autenticação JWT Bearer Token (automática após login)
- ✅ Métricas calculadas automaticamente pelo sistema
- ✅ Rastreamento de séries a nível individual
- ✅ Suporte para RPE, notas e tempo de descanso por série
- ✅ Cascading deletes (deletar workout remove exercícios e séries)
- ✅ Isolamento de dados por usuário

---

**API Base URL:** `http://localhost:8000`
**Documentação Interativa:** `http://localhost:8000/docs`
**Versão da API:** 1.0.0
