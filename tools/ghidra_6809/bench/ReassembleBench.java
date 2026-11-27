import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.plugin.assembler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.io.*; import java.nio.file.*; import java.util.*;
public class ReassembleBench extends GhidraScript {
  public void run() throws Exception {
    String[] a = getScriptArgs();
    Assembler asm = Assemblers.getAssembler(currentProgram);
    List<long[]> entries = new ArrayList<>(); List<String> names = new ArrayList<>();
    List<String> bad = new ArrayList<>();
    List<String> lines = Files.readAllLines(Paths.get(a[0]));
    String fn = null; long ent = 0; List<Object[]> cur = null;
    Map<String,List<Object[]>> fs = new LinkedHashMap<>(); Map<String,Long> ents = new HashMap<>();
    for (String l : lines) {
      if (l.startsWith("F ")) { String[] p = l.split(" "); fn = p[1]+" "+p[2]; cur = new ArrayList<>(); fs.put(fn, cur); ents.put(fn, Long.parseLong(p[1],16)); }
      else if (!l.isBlank()) { String[] p = l.split("\t"); cur.add(new Object[]{Long.parseLong(p[0],16), p[1]}); }
    }
    int asmFail = 0;
    for (var e : fs.entrySet()) {
      List<Object[]> ins = e.getValue(); 
      for (int i=0;i<ins.size();i++) { Address ad = toAddr((Long)ins.get(i)[0]);
        try { asm.assemble(ad, (String)ins.get(i)[1]); } catch (Exception ex) { asmFail++; bad.add(e.getKey()+" "+ad+" "+ins.get(i)[1]+" :: "+ex.getMessage().split("\n")[0]); } }
      for (int i=0;i+1<ins.size();i++) { Instruction in = getInstructionAt(toAddr((Long)ins.get(i)[0])); if (in==null) continue;
        Address nx = toAddr((Long)ins.get(i+1)[0]);
        if (in.getFlowType().hasFallthrough() && !in.getFallThrough().equals(nx)) in.setFallThrough(nx); }
      createFunction(toAddr(ents.get(e.getKey())), e.getKey().split(" ")[1]);
    }
    DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
    int ok=0, fail=0; StringBuilder rep = new StringBuilder();
    boolean dump = a.length>1 && a[1].equals("dump");
    for (Function f : currentProgram.getListing().getFunctions(true)) {
      DecompileResults r = di.decompileFunction(f, 30, monitor);
      boolean good = r.decompileCompleted();
      if (good) ok++; else fail++;
      println("RESULT " + f.getEntryPoint() + " " + f.getName() + " " + (good?"OK":"FAIL "+r.getErrorMessage()));
      if (good && dump) println("CODE<<\n"+r.getDecompiledFunction().getC()+">>CODE");
    }
    for (String b: bad) println("ASMFAIL "+b);
    println("SUMMARY ok="+ok+" fail="+fail+" asmfail="+asmFail);
  }
}
