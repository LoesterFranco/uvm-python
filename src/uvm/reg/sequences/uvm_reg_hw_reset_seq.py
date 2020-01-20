#//
#// -------------------------------------------------------------
#//    Copyright 2004-2008 Synopsys, Inc.
#//    Copyright 2010 Mentor Graphics Corporation
#//    Copyright 2019 Tuomas Poikela (tpoikela)
#//    All Rights Reserved Worldwide
#//
#//    Licensed under the Apache License, Version 2.0 (the
#//    "License"); you may not use this file except in
#//    compliance with the License.  You may obtain a copy of
#//    the License at
#//
#//        http://www.apache.org/licenses/LICENSE-2.0
#//
#//    Unless required by applicable law or agreed to in
#//    writing, software distributed under the License is
#//    distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
#//    CONDITIONS OF ANY KIND, either express or implied.  See
#//    the License for the specific language governing
#//    permissions and limitations under the License.
#// -------------------------------------------------------------
#//

import cocotb

from ...macros import uvm_object_utils, uvm_info, uvm_error
from .. import uvm_reg_sequence
from ...base.uvm_resource_db import UVMResourceDb
from ...base.sv import sv
from ...base import UVM_LOW, UVM_HIGH
from ...base.uvm_globals import uvm_empty_delay
from ..uvm_reg_model import UVM_CHECK, UVM_FRONTDOOR, UVM_IS_OK

#//
#// class: uvm_reg_hw_reset_seq
#// Test the hard reset values of registers
#//
#// The test sequence performs the following steps
#//
#// 1. resets the DUT and the
#// block abstraction class associated with this sequence.
#//
#// 2. reads all of the registers in the block,
#// via all of the available address maps,
#// comparing the value read with the expected reset value.
#//
#// If bit-type resource named
#// "NO_REG_TESTS" or "NO_REG_HW_RESET_TEST"
#// in the "REG::" namespace
#// matches the full name of the block or register,
#// the block or register is not tested.
#//
#//| UVMResourceDb#(bit)::set({"REG::",regmodel.blk.get_full_name(),".*"},
#//|                            "NO_REG_TESTS", 1, this)
#//
#// This is usually the first test executed on any DUT.
#//


class uvm_reg_hw_reset_seq(uvm_reg_sequence):  # (uvm_sequence #(uvm_reg_item))

    def __init__(self, name="uvm_reg_hw_reset_seq"):
        super().__init__(name)
        #   // Variable: model
        #   //
        #   // The block to be tested. Declared in the base class.
        #   //
        self.model = None  # uvm_reg_block


    #   // Variable: body
    #   //
    #   // Executes the Hardware Reset sequence.
    #   // Do not call directly. Use seq.start() instead.
    #
    @cocotb.coroutine
    def body(self):
        if self.model is None:
            uvm_error("uvm_reg_hw_reset_seq", "Not block or system specified to run sequence on")
            return
        uvm_info("STARTING_SEQ", "|uvm_reg_hw_reset_seq| Starting " + self.get_name() +
                " sequence...",UVM_LOW)

        yield self.reset_blk(self.model)
        self.model.reset()

        yield self.do_block(self.model)
    #   endtask: body

    #// Task: do_block
    #   //
    #   // Test all of the registers in a given ~block~
    #   //
    #   protected virtual task do_block(uvm_reg_block blk)
    @cocotb.coroutine
    def do_block(self, blk):
        maps = []  # uvm_reg_map maps[$]
        sub_maps = []  # uvm_reg_map sub_maps[$]
        no_rr1 = UVMResourceDb.get_by_name("REG::" + blk.get_full_name(), "NO_REG_TESTS", 0)
        no_rr2 = UVMResourceDb.get_by_name("REG::" + blk.get_full_name(), "NO_REG_HW_RESET_TEST", 0)

        print("reg_hw_reset Do block started " + str(no_rr1) + ' ' + str(no_rr2))
        print("blk_name is " + blk.get_full_name())
        if no_rr1 is not None or no_rr2 is not None:
            return

        blk.get_maps(maps)
        # Iterate over all maps defined for the RegModel block
        #
        for d in range(len(maps)):
            #uvm_reg regs[$]
            regs = []
            maps[d].get_submaps(sub_maps)
            if len(sub_maps) != 0:
                continue

            # Iterate over all registers in the map, checking accesses
            # Note: if map were in inner loop, could test simulataneous
            # access to same reg via different bus interfaces

            regs = []
            maps[d].get_registers(regs)

            for i in range(len(regs)):
                #uvm_status_e status
                status = 0

                reg_name = regs[i].get_full_name()
                print("Iterating now over reset " + reg_name)
                # Registers with certain attributes are not to be tested
                dont_test1 = UVMResourceDb.get_by_name("REG::" + regs[i].get_full_name(), "NO_REG_HW_RESET_TEST", 0)
                dont_test2 = UVMResourceDb.get_by_name("REG::" + regs[i].get_full_name(), "NO_REG_TESTS", 0)
                if (dont_test1 is not None or dont_test2 is not None):
                    continue

                uvm_info(self.get_type_name(),
                        sv.sformatf("Verifying reset value of register %s in map \"%s\"...",
                            regs[i].get_full_name(), maps[d].get_full_name()), UVM_LOW)

                status = []
                yield regs[i].mirror(status, UVM_CHECK, UVM_FRONTDOOR, maps[d], self)
                status = status[0]

                if status != UVM_IS_OK:
                    uvm_error(self.get_type_name(),
                          sv.sformatf("Status was %s when reading reset value of register \"%s\" through map \"%s\".",
                          status.name(), regs[i].get_full_name(), maps[d].get_full_name()))

            blks = []  # uvm_reg_block blks[$]
            blk.get_blocks(blks)
            for i in range(len(blks)):
                yield self.do_block(blks[i])

        #   endtask:do_block

    #   // task: reset_blk
    #   // Reset the DUT that corresponds to the specified block abstraction class.
    #   //
    #   // Currently empty.
    #   // Will rollback the environment's phase to the ~reset~
    #   // phase once the new phasing is available.
    #   //
    #   // In the meantime, the DUT should be reset before executing this
    #   // test sequence or this method should be implemented
    #   // in an extension to reset the DUT.
    #   //
    #   virtual task reset_blk(uvm_reg_block blk)
    @cocotb.coroutine
    def reset_blk(self, blk):
        yield uvm_empty_delay()

    #endclass: uvm_reg_hw_reset_seq
uvm_object_utils(uvm_reg_hw_reset_seq)