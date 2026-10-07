import {defineConfig, type Plugin} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import {resolve} from 'node:path';

// Browser development only: same-origin, loopback bridge to the real sidecar.
// Packaged builds use Tauri IPC and expose no network listener.
function pythonPreview(): Plugin {
  return {name:'python-preview', configureServer(server) {
    if(process.env.TAURI_ENV_PLATFORM) return;
    const python = resolve('../.venv/Scripts/python.exe');
    const args = ['-u', resolve('../app/desktop_service.py')];
    if(process.env.JEV_TRADER_DATA_DIR) args.push('--data-dir', process.env.JEV_TRADER_DATA_DIR);
    const child = spawn(python,args,{stdio:['pipe','pipe','ignore'],windowsHide:true});
    const pending = new Map<string,(value:unknown)=>void>();
    createInterface({input:child.stdout}).on('line',line=>{try{
      const message=JSON.parse(line);
      if(message.id && pending.has(message.id)) {pending.get(message.id)!(message);pending.delete(message.id);}
      else server.ws.send({type:'custom',event:'engine',data:message});
    }catch{/* invalid sidecar lines are never executed */}});
    const stop=()=>{child.stdin.end(); setTimeout(()=>child.kill(),1000).unref();};
    server.httpServer?.once('close',stop);
    process.once('exit',()=>child.kill());
    server.middlewares.use('/__engine',(req,res)=>{
      if(req.method!=='POST' || req.headers.origin!==`http://${req.headers.host}`) {res.statusCode=403;res.end();return;}
      let body='';req.on('data',chunk=>{body+=chunk;if(body.length>65536)req.destroy();});
      req.on('end',()=>{try{
        const message=JSON.parse(body);
        const timeout=setTimeout(()=>{pending.delete(message.id);res.statusCode=504;res.end();},10000);
        pending.set(message.id,value=>{clearTimeout(timeout);res.setHeader('Content-Type','application/json');res.end(JSON.stringify(value));});
        child.stdin.write(JSON.stringify(message)+'\n');
      }catch{res.statusCode=400;res.end();}});
    });
  }};
}
export default defineConfig({plugins:[react(),tailwindcss(),pythonPreview()],clearScreen:false,server:{port:1420,strictPort:true,host:'127.0.0.1'},build:{target:'es2022'}});
