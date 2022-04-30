<template>
  <div class="error-message">
    <v-row>
      <v-col cols="12">
        <v-alert border="left" color="red">
          {{errorMessage}}
        </v-alert>
      </v-col>
    </v-row>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { AxiosError } from 'axios';

export default Vue.extend({
  name: 'ErrorMessage',
  props: {
    error: {
      required: true,
    }
  },
  computed: {
    errorMessage(): string {
      if (this.error && (this.error as AxiosError).response) {
        if ((this.error as AxiosError).response?.status === 403) {
          return 'Access denied! Try one of your own things.';
        }
      }
      this.$store.commit('snackbar/showError', this.error);
      return 'Failed to load....';
    }
  }
})
</script>