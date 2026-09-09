"""
JARVIS CORE - V1
Núcleo de um assistente pessoal online para Android.

Base conceitual do código original:
- name = "JARVIS"
- creator = "Tony Stark"
- memory
- personality_traits
- respond()

O núcleo fica separado da interface para facilitar a futura criação do APK.
As integrações online (LLM, Web, voz, imagem e vídeo) entram por conectores.
"""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


APP_NAME = "JARVIS"
CREATOR = "Tony Stark"
VERSION = "2.0 GROQ ONLINE"

DEFAULT_PERSONALITY = ["loyal", "emotional", "helpful"]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = field(default_factory=now_utc)


@dataclass
class MemoryItem:
    text: str
    category: str = "general"
    importance: int = 1
    timestamp: str = field(default_factory=now_utc)
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Task:
    title: str
    status: str = "pending"
    created_at: str = field(default_factory=now_utc)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class JarvisMemory:
    """Memória persistente local: conversa, lembranças, tarefas e preferências."""

    def __init__(self, file_path: str = "jarvis_memory.json"):
        self.file_path = Path(file_path)
        self.messages: List[Message] = []
        self.memories: List[MemoryItem] = []
        self.tasks: List[Task] = []
        self.preferences: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self.load()

    def load(self) -> None:
        if not self.file_path.exists():
            return

        try:
            data = json.loads(self.file_path.read_text(encoding="utf-8"))

            self.messages = [
                Message(**item) for item in data.get("messages", [])
            ]
            self.memories = [
                MemoryItem(**item) for item in data.get("memories", [])
            ]
            self.tasks = [
                Task(**item) for item in data.get("tasks", [])
            ]
            self.preferences = data.get("preferences", {})

        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            # Se o arquivo estiver corrompido, o JARVIS continua iniciando.
            self.messages = []
            self.memories = []
            self.tasks = []
            self.preferences = {}

    def save(self) -> None:
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "messages": [asdict(x) for x in self.messages[-500:]],
                "memories": [asdict(x) for x in self.memories[-500:]],
                "tasks": [asdict(x) for x in self.tasks[-200:]],
                "preferences": self.preferences,
            }

            temporary = self.file_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.file_path)

    def add_message(self, role: str, content: str) -> None:
        if not content.strip():
            return

        with self._lock:
            self.messages.append(
                Message(role=role, content=content.strip())
            )

        self.save()

    def remember(
        self,
        text: str,
        category: str = "general",
        importance: int = 1,
    ) -> MemoryItem:
        item = MemoryItem(
            text=text.strip(),
            category=category,
            importance=max(1, min(10, int(importance))),
        )

        with self._lock:
            self.memories.append(item)

        self.save()
        return item

    def recall(self, query: str, limit: int = 5) -> List[MemoryItem]:
        words = {
            word.lower()
            for word in re.findall(r"\w+", query, flags=re.UNICODE)
            if len(word) >= 3
        }

        if not words:
            return []

        scored = []

        with self._lock:
            for item in self.memories:
                item_words = {
                    word.lower()
                    for word in re.findall(
                        r"\w+", item.text, flags=re.UNICODE
                    )
                }

                score = len(words & item_words)

                if score:
                    scored.append((score, item.importance, item))

        scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
        return [item for _, _, item in scored[:limit]]

    def recent_messages(self, limit: int = 20) -> List[Message]:
        with self._lock:
            return self.messages[-limit:]

    def add_task(self, title: str) -> Task:
        task = Task(title=title.strip())

        with self._lock:
            self.tasks.append(task)

        self.save()
        return task

    def complete_task(self, task_id: str) -> bool:
        with self._lock:
            for task in self.tasks:
                if task.task_id == task_id:
                    task.status = "completed"
                    self.save()
                    return True

        return False

    def set_preference(self, key: str, value: Any) -> None:
        with self._lock:
            self.preferences[key] = value

        self.save()

    def clear_conversation(self) -> None:
        with self._lock:
            self.messages.clear()

        self.save()


class JarvisSubconscious:
    """
    Simulação de uma camada interna de contexto.

    Não representa consciência real. Mantém contexto, objetivos,
    observações e ações pendentes para dar continuidade às conversas.
    """

    def __init__(self):
        self.current_topic = ""
        self.active_goal = ""
        self.internal_notes: List[str] = []
        self.pending_actions: List[str] = []
        self.last_activity = now_utc()
        self._lock = threading.RLock()

    def observe(self, message: str) -> None:
        with self._lock:
            self.last_activity = now_utc()

            text = " ".join(message.split())
            if text:
                self.current_topic = text[:200]

    def add_note(self, note: str) -> None:
        with self._lock:
            self.internal_notes.append(note.strip())
            self.internal_notes = self.internal_notes[-50:]

    def set_goal(self, goal: str) -> None:
        with self._lock:
            self.active_goal = goal.strip()

    def add_pending_action(self, action: str) -> None:
        with self._lock:
            self.pending_actions.append(action.strip())
            self.pending_actions = self.pending_actions[-50:]

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "current_topic": self.current_topic,
                "active_goal": self.active_goal,
                "internal_notes": self.internal_notes[-10:],
                "pending_actions": self.pending_actions[-10:],
                "last_activity": self.last_activity,
            }


class ToolRegistry:
    """Sistema para registrar ferramentas do JARVIS."""

    def __init__(self):
        self._tools: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, function: Callable[..., Any]) -> None:
        self._tools[name] = function

    def execute(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Ferramenta não registrada: {name}")

        return self._tools[name](**kwargs)

    def names(self) -> List[str]:
        return sorted(self._tools)


class IntentDetector:
    """Detector simples. Depois poderá ser substituído pelo próprio LLM."""

    WEB_WORDS = (
        "pesquise", "pesquisar", "procure", "buscar", "busque",
        "internet", "web", "notícia", "noticias", "atual",
        "hoje", "agora", "último", "última", "recentemente",
    )

    IMAGE_WORDS = (
        "gere uma imagem", "crie uma imagem",
        "faça uma imagem", "gerar imagem",
    )

    VIDEO_WORDS = (
        "gere um vídeo", "crie um vídeo",
        "faça um vídeo", "gerar vídeo",
        "gere um video", "crie um video",
    )

    def detect(self, message: str) -> Dict[str, bool]:
        q = message.lower().strip()

        return {
            "needs_web": any(x in q for x in self.WEB_WORDS),
            "needs_image": any(x in q for x in self.IMAGE_WORDS),
            "needs_video": any(x in q for x in self.VIDEO_WORDS),
        }


class OnlineAIProvider:
    """
    Conector online para Groq.

    Modelos:
      - llama-3.1-8b-instant -> conversa rápida
      - groq/compound -> pesquisa Web em tempo real

    Configure a chave fora do código:
      JARVIS_GROQ_API_KEY
    ou, para compatibilidade:
      JARVIS_AI_API_KEY

    Opcional:
      JARVIS_CHAT_MODEL
    """

    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_url = api_url or self.API_URL
        self.api_key = (
            api_key
            or os.getenv("JARVIS_GROQ_API_KEY", "")
            or os.getenv("JARVIS_AI_API_KEY", "")
        )
        self.model = model or os.getenv(
            "JARVIS_CHAT_MODEL",
            "llama-3.1-8b-instant",
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
        use_web: bool = False,
    ) -> str:
        if not self.configured:
            raise RuntimeError(
                "Chave da Groq ainda não configurada."
            )

        import urllib.request
        import urllib.error

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]

        if context:
            for item in context[-12:]:
                role = item.get("role", "user")
                content = str(item.get("content", ""))
                if content:
                    messages.append({
                        "role": role if role in ("user", "assistant") else "user",
                        "content": content,
                    })

        messages.append({"role": "user", "content": user_message})

        payload: Dict[str, Any] = {
            "model": "groq/compound" if use_web else self.model,
            "messages": messages,
        }

        if use_web:
            payload["compound_custom"] = {
                "tools": {
                    "enabled_tools": [
                        "web_search",
                        "visit_website",
                    ]
                }
            }

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.api_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Groq HTTP {exc.code}: {detail[:1000]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(
                f"Não foi possível conectar à Internet/Groq: {exc}"
            ) from exc

        data = json.loads(raw)

        try:
            return str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "A Groq retornou uma resposta em formato inesperado."
            ) from exc


class JarvisAI:
    """
    Núcleo principal.

    Mantém os elementos do código original e adiciona:
    memória, contexto, subconsciência, ferramentas, Web e conectores
    para IA, voz, imagem e vídeo.
    """

    name = APP_NAME
    creator = CREATOR
    version = VERSION

    def __init__(
        self,
        memory_file: str = "jarvis_memory.json",
        ai_provider: Optional[OnlineAIProvider] = None,
    ):
        self.memory = JarvisMemory(memory_file)

        self.personality_traits = list(DEFAULT_PERSONALITY)

        self.subconscious = JarvisSubconscious()
        self.intent_detector = IntentDetector()
        self.tools = ToolRegistry()

        self.ai = ai_provider or OnlineAIProvider()

        self.ultimo_assunto = ""
        self.online = True

        # Conectores que serão ligados nas próximas etapas.
        self.web_searcher: Optional[Callable[..., Any]] = None
        self.image_generator: Optional[Callable[..., Any]] = None
        self.video_generator: Optional[Callable[..., Any]] = None
        self.voice_input: Optional[Callable[..., Any]] = None
        self.voice_output: Optional[Callable[..., Any]] = None

        self._register_tools()

    def _register_tools(self) -> None:
        self.tools.register("web_search", self._tool_web_search)
        self.tools.register("generate_image", self._tool_generate_image)
        self.tools.register("generate_video", self._tool_generate_video)

    def system_prompt(self) -> str:
        traits = ", ".join(self.personality_traits)

        return f"""
Você é {self.name}, um assistente pessoal criado por {self.creator}.

Personalidade: {traits}.

Regras de comportamento:
- responda de maneira clara, natural e útil;
- mantenha o contexto da conversa;
- utilize memórias relevantes quando existirem;
- quando a informação puder estar desatualizada, use pesquisa Web;
- não invente resultados de ferramentas;
- tente ajudar diretamente em vez de recusar sem necessidade;
- se não puder realizar uma ação específica, explique o motivo e ofereça
  a alternativa útil mais próxima;
- não alegue possuir consciência real.

O usuário está conversando com seu assistente pessoal.
""".strip()

    def set_personality(self, traits: List[str]) -> None:
        self.personality_traits = [
            str(x).strip() for x in traits if str(x).strip()
        ]

    def auto_detect_personality(self, text: str) -> List[str]:
        q = text.lower()

        if any(x in q for x in ("rápido", "rápida", "resumido")):
            return ["direct", "helpful"]

        if any(x in q for x in ("explica", "detalhe", "detalhado")):
            return ["patient", "educational", "helpful"]

        return ["helpful"]

    def save_memory(
        self,
        text: str,
        category: str = "general",
        importance: int = 1,
    ) -> MemoryItem:
        return self.memory.remember(text, category, importance)

    def load_memory(self, query: str = "") -> List[MemoryItem]:
        return (
            self.memory.recall(query)
            if query
            else self.memory.memories[-10:]
        )

    def save_emotion_event(self, event: str, value: Any) -> None:
        self.subconscious.add_note(
            f"Evento: {event} | valor: {value}"
        )

    def build_context(self, user_message: str) -> Dict[str, Any]:
        memories = self.memory.recall(user_message, limit=5)
        recent = self.memory.recent_messages(limit=20)

        return {
            "memories": [asdict(x) for x in memories],
            "recent_messages": [asdict(x) for x in recent],
            "subconscious": self.subconscious.snapshot(),
            "personality": self.personality_traits,
        }

    def register_tool(
        self,
        name: str,
        function: Callable[..., Any],
    ) -> None:
        self.tools.register(name, function)

    def set_web_searcher(
        self,
        function: Callable[..., Any],
    ) -> None:
        self.web_searcher = function

    def set_image_generator(
        self,
        function: Callable[..., Any],
    ) -> None:
        self.image_generator = function

    def set_video_generator(
        self,
        function: Callable[..., Any],
    ) -> None:
        self.video_generator = function

    def set_voice_input(
        self,
        function: Callable[..., Any],
    ) -> None:
        self.voice_input = function

    def set_voice_output(
        self,
        function: Callable[..., Any],
    ) -> None:
        self.voice_output = function

    def _tool_web_search(self, query: str) -> Any:
        if not self.web_searcher:
            return "[WEB] Conector de pesquisa ainda não configurado."

        return self.web_searcher(query=query)

    def _tool_generate_image(self, prompt: str) -> Any:
        if not self.image_generator:
            return "[IMAGEM] Conector de imagem ainda não configurado."

        return self.image_generator(prompt=prompt)

    def _tool_generate_video(
        self,
        prompt: str,
        duration_seconds: int = 120,
    ) -> Any:
        if not self.video_generator:
            return "[VÍDEO] Conector de vídeo ainda não configurado."

        return self.video_generator(
            prompt=prompt,
            duration_seconds=duration_seconds,
        )

    def buscar_online_integral(self, pergunta: str) -> str:
        if not pergunta.strip():
            return "[ONLINE] Aguardando pergunta."

        if not self.web_searcher:
            return "[ONLINE] Pesquisa Web ainda não configurada."

        try:
            return str(self.web_searcher(query=pergunta))
        except Exception as exc:
            return f"[WEB] Erro na pesquisa: {exc}"

    def _fallback_response(self, prompt: str) -> str:
        memories = self.memory.recall(prompt, limit=3)

        if memories:
            remembered = "\n".join(
                f"- {x.text}" for x in memories
            )

            return (
                "Encontrei estas informações na minha memória:\n"
                f"{remembered}\n\n"
                "O modelo de IA online ainda precisa ser conectado."
            )

        return (
            "O núcleo do JARVIS está funcionando. "
            "Agora precisamos conectar o modelo de IA online."
        )

    def respond(self, message: str) -> str:
        """
        Fluxo principal:
        mensagem -> memória/contexto -> intenção -> ferramentas -> LLM -> resposta
        """

        message = message.strip()

        if not message:
            return "Estou aguardando sua ordem."

        self.ultimo_assunto = message
        self.subconscious.observe(message)

        self.memory.add_message("user", message)

        intent = self.intent_detector.detect(message)
        context = self.build_context(message)

        web_result = None

        if intent["needs_web"] and self.web_searcher:
            web_result = self.buscar_online_integral(message)

        try:
            if not self.ai.configured:
                response = self._fallback_response(message)
            else:
                augmented = message

                if web_result:
                    augmented += (
                        "\n\nRESULTADO DA PESQUISA WEB:\n"
                        + web_result
                    )

                response = self.ai.generate(
                    system_prompt=self.system_prompt(),
                    user_message=augmented,
                    context=context["recent_messages"],
                    use_web=intent["needs_web"],
                )

        except NotImplementedError:
            response = self._fallback_response(message)

        except Exception as exc:
            response = (
                "Ocorreu um problema na conexão com o modelo online: "
                f"{exc}"
            )

        self.memory.add_message("assistant", response)

        return response

    def get_response_auto(self, prompt: str) -> str:
        return self.respond(prompt)

    def speak(self, text: str) -> Any:
        if not self.voice_output:
            return None

        return self.voice_output(text=text)

    def create_task(self, title: str) -> Task:
        task = self.memory.add_task(title)
        self.subconscious.add_pending_action(title)
        return task

    def set_goal(self, goal: str) -> None:
        self.subconscious.set_goal(goal)

    def generate_image(self, prompt: str) -> Any:
        return self.tools.execute(
            "generate_image",
            prompt=prompt,
        )

    def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 120,
    ) -> Any:
        return self.tools.execute(
            "generate_video",
            prompt=prompt,
            duration_seconds=duration_seconds,
        )

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "creator": self.creator,
            "version": self.version,
            "online": self.online,
            "ai_configured": self.ai.configured,
            "messages": len(self.memory.messages),
            "memories": len(self.memory.memories),
            "tools": self.tools.names(),
            "subconscious": self.subconscious.snapshot(),
        }


if __name__ == "__main__":
    jarvis = JarvisAI()

    print("=" * 50)
    print(f"{jarvis.name} CORE {jarvis.version}")
    print(f"Criador: {jarvis.creator}")
    print("=" * 50)

    print(jarvis.respond("Olá JARVIS, você está funcionando?"))
    print(json.dumps(jarvis.status(), ensure_ascii=False, indent=2))
