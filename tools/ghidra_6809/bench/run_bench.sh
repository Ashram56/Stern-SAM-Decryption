#!/bin/sh
# run_bench.sh GHIDRA_DIR BATCH_FILE [dump]  (RESULT per function, SUMMARY ok= fail=)
G=$1; D=${TMPDIR:-/tmp}/rbench_$$; mkdir -p $D; head -c 65536 /dev/zero > $D/z.bin
"$G/support/analyzeHeadless" $D p -import $D/z.bin -overwrite -loader BinaryLoader -loader-baseAddr 0 -processor ${LANG6809:-6809:BE:16:default} -scriptPath $(cd "$(dirname "$0")" && pwd) -postScript ReassembleBench.java $2 $3 2>&1 | grep -E "RESULT|ASMFAIL|SUMMARY|CODE|^\s*(void|undefined|int|char|byte|uint)|ERROR|Exception"
rm -rf $D
