#!/usr/bin/env python3
"""Add "@bot" to T3 Code's citation comment popover.

Select assistant text -> Comment -> type "@bot <instruction>" -> Enter.
The citation (origin env/thread/message ids + quoted text) and the instruction
go to the local relay on 127.0.0.1, which forwards them to Grok Bot. The
running thread and its composer are never touched. Without a leading "@bot",
Save / Cmd+Enter behave exactly as stock. An "@bot" button sends the same way.

Every anchor must occur exactly once in the input module, or nothing is written.
"""
import sys

MARK = '__t3botSend'
PORT = 47811

HELPERS = (
    'function __t3botIs(e){return/^\\s*@bot\\b/i.test(String(e??""))}'
    'function __t3botToast(m,err,ms){try{let d=document.getElementById("t3bot-toast");'
    'if(!d){d=document.createElement("div");d.id="t3bot-toast";d.setAttribute("role","status");'
    'd.style.cssText="position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:420px;padding:8px 12px;'
    'border-radius:8px;font:13px system-ui,sans-serif;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.3);pointer-events:none";'
    'document.body.appendChild(d)}d.textContent=m;d.style.background=err?"#7f1d1d":"#1f2937";'
    'clearTimeout(d._t);d._t=setTimeout(()=>d.remove(),ms||(err?7000:15000))}catch{}}'
    'function __t3botSend(raw,ref){let x=ref&&ref.current,'
    't=String(raw??"").replace(/^\\s*(?:@bot\\b[\\s,:]*)+/i,"").trim();'
    'if(!x||!x.c){__t3botToast("@bot: no citation to send",1);return!0}'
    'if(!t){__t3botToast("@bot: write the instruction after @bot",1);return!0}'
    'let c=x.c,b={environmentId:x.e??c.environmentId,projectId:x.p??null,threadId:c.threadId,'
    'messageId:c.messageId,quote:c.text,quoteStart:c.start,quoteEnd:c.end,request:t};'
    '__t3botToast("Sending to @bot\\u2026",0);'
    f'fetch("http://127.0.0.1:{PORT}/cite",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(b)}})'
    '.then(async r=>{let j={};try{j=await r.json()}catch{}'
    'if(r.ok&&j.ok){__t3botToast(j.duplicate?"Already sent to @bot":"Sent to @bot",0,2500);try{ref.current?.x?.()}catch{}}'
    'else __t3botToast("@bot failed: "+(j.error||"HTTP "+r.status),1)})'
    f'.catch(()=>__t3botToast("@bot relay is not running (127.0.0.1:{PORT})",1));return!0}}'
)

EDITS = [
    # Module helpers, placed just before the citation comment editor component.
    ('function aS(e){', HELPERS + 'function aS(e){'),
    # A stable per-editor ref with the current citation, ids and close callback,
    # so memoized handlers never read a stale citation.
    ('let g=h,_=p??n.environmentId,v;',
     'let g=h,_=p??n.environmentId,v,__br=(0,V.useRef)(null);__br.current={c:n,e:_,p:m,x:o};'),
    # Enter (save): "@bot ..." goes to the relay instead of the composer.
    ('e.length<=8e3&&i(e)})',
     'e.length<=8e3&&(__t3botIs(e)?__t3botSend(e,__br):i(e))})'),
    # Cmd/Ctrl+Enter (save and send): same routing.
    ('e.length<=8e3&&(a??i)(e)})',
     'e.length<=8e3&&(__t3botIs(e)?__t3botSend(e,__br):(a??i)(e))})'),
    # Visible "@bot" button between Cancel and Save.
    ('children:[L,R,te]',
     'children:[L,R,(0,H.jsx)(Ue,{variant:`outline`,size:`xs`,tabIndex:-1,onPointerDown:sS,'
     'onClick:()=>__t3botSend(f.current?.value??``,__br),children:`@bot`}),te]'),
]


def is_target(source):
    return MARK not in source and all(source.count(a) == 1 for a, _ in EDITS)


def is_patched(source):
    return MARK in source and all(source.count(b) == 1 for _, b in EDITS[1:])


def patch(source):
    if is_patched(source):
        return source
    missing = [a for a, _ in EDITS if source.count(a) != 1]
    if missing:
        raise ValueError('Unrecognized frontend; anchors not unique/present: %r' % missing)
    for before, after in EDITS:
        source = source.replace(before, after, 1)
    if not is_patched(source):
        raise ValueError('Patch verification failed')
    return source


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    data = open(src, encoding='utf-8').read()
    open(dst, 'w', encoding='utf-8').write(patch(data))
    print('patched', dst)
