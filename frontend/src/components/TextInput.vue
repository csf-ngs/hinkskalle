<template>
  <div>
    <v-text-field v-if="type=='text'"
      outlined
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" :append-icon="readonly || localState.static ? 'mdi-lock-outline' : ''"
      @change="saveValue()"
    ></v-text-field>
    <v-textarea v-if="type=='textarea'"
      outlined
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" :append-icon="readonly || localState.static ? 'mdi-lock-outline' : ''"
      @change="saveValue()"
    ></v-textarea>
    <v-select v-if="type=='yesno'"
      outlined
      v-model="localState.value"
      :label="label"
      :loading="localState.status=='saving'"
      :success="localState.status=='success'"
      :error="localState.status=='failed'"
      :disabled="disabled"
      :readonly="localState.static || readonly" :append-icon="readonly || localState.static ? 'mdi-lock-outline' : ''"
      :items="[ { value: false, text: 'No' }, { value: true, text: 'Yes' } ]"
      @change="saveValue()"
    ></v-select>
  </div>
  
</template>
<script lang="ts">
import Vue from 'vue';

// :append-icon="localState.static ? 'mdi-lock-outline' : null"

import { clone as _clone } from 'lodash';

interface State {
  status: string;
  value: string;
  static: boolean;
}

export default Vue.extend({
  name: 'HinkTextInput',
  props: {
    type: {
      type: String,
      default: "text",
    }, 
    label: {
      type: String,
      required: true,
    },
    field: String,
    obj: Object,
    action: String,
    readonly: Boolean,
    disabled: Boolean,
    staticValue: {
      type: [ String, Boolean, Number ],
      default: undefined,
    },
  },
  data: function(): { localState: State } {
    return {
      localState: {
        status: '',
        value: this.obj && this.field ? this.obj[this.field] : this.staticValue,
        static: this.staticValue !== undefined
      }
    };
  },
  watch: {
    field(newVal, oldVal) {
      if (this.obj && this.field) {
        this.localState.value=this.obj[this.field];
      }
    },
    obj(newVal, oldVal) {
      if (this.obj && this.field) {
        this.localState.value=this.obj[this.field];
      }
    },
    staticValue(newVal, oldVal) {
      this.localState.value=newVal;
      this.localState.static = newVal !== undefined;
    },
  },
  methods: {
    saveValue() {
      const obj = _clone(this.obj);
      obj[this.field] = this.localState.value;
      if (!this.action) {
        return this.$emit('updated', obj);
      }
      this.localState.status='saving';
      this.$store.dispatch(this.action, obj)
        .then(updated => {
          this.localState.status='success';
          this.$emit('updated', updated);
        })
        .catch(err => {
          this.localState.status='failed';
          this.$store.commit('snackbar/showError', err);
        });
    }
  },
})
</script>