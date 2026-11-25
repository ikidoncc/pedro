(function(){
  'use strict';
  const selector = [
    '.preview-card', '.analysis-value', '.exercise-prompt', '.exercise-options',
    '.algebra-step-card', '.syntax-card', '.exercise-solution', '.property-info',
    '.neoex-canvas-math', '.neoex-canvas-domain-math', '.domain-preview-formula',
    '.math-preview-formula', '.counter'
  ].join(',');
  const pending = new Set();
  let observer = null, mathReady = !!window.__NEOEX_MATHJAX_READY__;
  let flushing = false, scheduled = false, failed = false, fallbackTimer = null;

  function fallback(item){
    if(!item || !item.isConnected || item.dataset.neoexMathRendered === 'fallback') return;
    const value = item.getAttribute('data-neoex-tex-fallback');
    if(value === null) return;
    item.textContent = value;
    item.classList.add('neoex-math-fallback');
    item.dataset.neoexMathRendered = 'fallback';
  }
  function failAll(){
    if(failed) return;
    failed = true;
    if(fallbackTimer !== null) clearTimeout(fallbackTimer);
    document.querySelectorAll('[data-neoex-tex-fallback]').forEach(fallback);
    pending.clear();
  }
  function collect(root){
    if(!root || root.nodeType !== 1) return;
    const add = item => {
      if(!item || !item.isConnected || item.dataset.neoexMathRendered === 'fallback' || item.dataset.neoexMathBusy === '1') return;
      pending.add(item);
    };
    if(root.matches && root.matches(selector)) add(root);
    if(root.querySelectorAll) root.querySelectorAll(selector).forEach(add);
  }
  function schedule(){
    if(!mathReady || failed || scheduled || flushing || !pending.size) return;
    scheduled = true;
    requestAnimationFrame(flush);
  }
  async function flush(){
    scheduled = false;
    if(!mathReady || failed || flushing) return;
    flushing = true;
    try{
      if(window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) await window.MathJax.startup.promise;
      while(pending.size){
        const batch = Array.from(pending); pending.clear();
        for(const item of batch){
          if(!item.isConnected || item.dataset.neoexMathRendered === 'fallback') continue;
          try{
            item.dataset.neoexMathBusy = '1';
            if(window.MathJax.typesetClear) window.MathJax.typesetClear([item]);
            await window.MathJax.typesetPromise([item]);
            item.dataset.neoexMathRendered = '1';
          }catch(error){
            console.warn('NEOEX: falha na renderização matemática.', error);
            fallback(item);
          }finally{ delete item.dataset.neoexMathBusy; }
        }
      }
    }catch(error){
      console.warn('NEOEX: MathJax não concluiu a inicialização.', error);
      failAll();
    }finally{ flushing = false; schedule(); }
  }
  function startObserver(){
    if(observer || !document.body) return;
    observer = new MutationObserver(records => {
      for(const record of records){
        const target = record.target && (record.target.nodeType === 1 ? record.target : record.target.parentElement);
        if(target && target.closest && target.closest('mjx-container,mjx-assistive-mml,.neoex-canvas-wrap,[data-neoex-math-busy="1"]')) continue;
        const added = Array.from(record.addedNodes || []);
        const onlyMathJax = added.length > 0 && added.every(node => node.nodeType === 1 && (
          (node.matches && node.matches('mjx-container,mjx-assistive-mml')) ||
          (node.querySelector && node.querySelector('mjx-container,mjx-assistive-mml'))
        ));
        if(onlyMathJax) continue;
        added.forEach(collect);
        if(target) collect(target);
      }
      schedule();
    });
    observer.observe(document.body, {childList:true, subtree:true});
    collect(document.documentElement);
  }
  function onReady(){
    if(!window.MathJax || !window.MathJax.typesetPromise) return;
    mathReady = true;
    if(fallbackTimer !== null) clearTimeout(fallbackTimer);
    startObserver(); collect(document.documentElement); schedule();
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', startObserver, {once:true});
  else startObserver();
  window.addEventListener('neoex-mathjax-ready', onReady);
  window.addEventListener('neoex-mathjax-failed', failAll, {once:true});
  if(window.__NEOEX_MATHJAX_READY__) onReady();
  fallbackTimer = setTimeout(() => { if(!mathReady) failAll(); }, 12000);
  window.NEOEX_typeset = function(root){ collect(root); schedule(); };
  window.NEOEX_mathFallback = failAll;

  // Auto-pair grouping delimiters in the algebra editor; Backspace remains native.
  document.addEventListener('keydown', function(event){
    const target = event.target;
    if(!target || !(target.matches('textarea') || target.matches('input')) || !target.closest('#neoex-algebra-input')) return;
    const pairs = {'(':')','[':']','{': '}'};
    const close = pairs[event.key];
    if(close && !event.ctrlKey && !event.metaKey && !event.altKey){
      const start = target.selectionStart, end = target.selectionEnd, value = target.value;
      event.preventDefault();
      target.setRangeText(event.key + value.slice(start,end) + close, start, end, 'end');
      target.setSelectionRange(start+1,start+1);
      target.dispatchEvent(new Event('input',{bubbles:true}));
      return;
    }
    if([')',']','}'].includes(event.key) && target.selectionStart === target.selectionEnd){
      const at = target.selectionStart;
      if(target.value[at] === event.key){ event.preventDefault(); target.setSelectionRange(at+1,at+1); }
    }
  }, true);
})();
