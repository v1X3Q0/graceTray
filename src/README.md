# commands for aiding in debugging

## isl

info shared library

Provide an address from a disassembly file, isl will translate it to the address of the current VA in its rebased address space.

Currently supports gdb and lldb, all archs.

### lldb

```
(lldb) isl vmware-vmx 1009be8e4
0x100a928e4
```



### gdb

## lta

locate target address

Provide an address from the active debug session, lta will do the opposite of isl and display the library its from and the offset.

Currently supports gdb and lldb, all archs.

### lldb

```
(lldb) lta 0x1a260c194
from libsystem_kernel.dylib.__TEXT offset 0x180394194
```

### gdb

## sbt

smart back trace

The backtrace command but a bit more intuitive, displaying the unslid file offset of the addresses, module and section associated.

Currently supports gdb and lldb, all archs.

### lldb

```
(lldb) sbt
0x1a260c194 libsystem_kernel.dylib.__TEXT 0x180394194::kevent
0x10010e380 mook.__TEXT 0x10003a380::___lldb_unnamed_symbol1841
0x100129484 mook.__TEXT 0x100055484::___lldb_unnamed_symbol2303
0x10010143c mook.__TEXT 0x10002d43c::___lldb_unnamed_symbol1600
0x100100874 mook.__TEXT 0x10002c874::___lldb_unnamed_symbol1598
0x1a231be50 dyld.__TEXT 0x1800a3e50::start
```

## stp

software tracepoint

Execution will trace each instruction executed until either a destination is reached, or the current frame is exited. The trace is done by saving the value of `$pc`. This command is necessary, at least for gdb, so that you can log instruction addresses to then display them in a disassembler to follow execution.

Currently supports `gdb` `arm32` and `x86_64`. `lldb` supports `arm64`. currently the only way to run arm64 is if you specify the funciton boundaries. This is because some routines would not restore the link register when they return, so I couldn't use that to continue, since the `lr == pc` and code execution would just loop.