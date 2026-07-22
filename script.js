// ============================================================
// AIDEA Dashboard — Demo Preview
// Tile navigation, chatbot toggle, copy-to-clipboard
// ============================================================

function openPanel(id, btn){
  document.querySelectorAll('.panel').forEach(function(p){ p.classList.remove('active'); });
  document.querySelectorAll('.tile').forEach(function(t){ t.classList.remove('active'); });

  var panel = document.getElementById(id);
  if(panel) panel.classList.add('active');
  if(btn) btn.classList.add('active');

  var contentPanel = document.querySelector('.content-panel');
  if(contentPanel) contentPanel.scrollIntoView({behavior:'smooth', block:'nearest'});
}

function copyCode(btnEl, codeId){
  var el = document.getElementById(codeId);
  if(!el) return;
  var text = el.innerText;
  navigator.clipboard.writeText(text).then(function(){
    var original = btnEl.textContent;
    btnEl.textContent = 'Copied';
    setTimeout(function(){ btnEl.textContent = original; }, 1400);
  }).catch(function(){
    /* clipboard API unavailable (e.g. file:// in some browsers) */
  });
}

// ---------- Chatbot (demo only, canned responses) ----------

var CANNED_REPLIES = [
  "That's a great question about RTL design — in a full build this would call the AI backend for a detailed answer.",
  "Good topic. This preview build doesn't have a live model connected, but the real AIDEA assistant would walk through that step by step.",
  "In the full version, I'd analyze your uploaded RTL to answer that precisely. For now, this is just the interface preview.",
];

function toggleChat(){
  var win = document.getElementById('chatbot-window');
  win.classList.toggle('open');
}

function sendChat(){
  var input = document.getElementById('chat-input-field');
  var body = document.getElementById('chat-body');
  var text = input.value.trim();
  if(!text) return;

  var userMsg = document.createElement('div');
  userMsg.className = 'msg user';
  userMsg.textContent = text;
  body.appendChild(userMsg);
  input.value = '';

  setTimeout(function(){
    var botMsg = document.createElement('div');
    botMsg.className = 'msg bot';
    botMsg.textContent = CANNED_REPLIES[Math.floor(Math.random() * CANNED_REPLIES.length)];
    body.appendChild(botMsg);
    body.scrollTop = body.scrollHeight;
  }, 500);

  body.scrollTop = body.scrollHeight;
}

document.addEventListener('DOMContentLoaded', function(){
  var input = document.getElementById('chat-input-field');
  if(input){
    input.addEventListener('keydown', function(e){
      if(e.key === 'Enter') sendChat();
    });
  }
});
