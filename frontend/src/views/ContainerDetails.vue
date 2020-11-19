<template>
  <div class="container-details">
    <top-bar :title="title"></top-bar>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { Container } from '../store/models';

interface State {
  container: Container | null;
}

export default Vue.extend({
  name: 'ContainerDetails',
  mounted() {
    this.loadContainer();
  },
  data: (): { localState: State } => ({
    localState: {
      container: null,
    }
  }),
  computed: {
    title(): string {
      return `Container Details for ${this.localState.container ? this.localState.container.fullPath : '...'}`
    }
  },
  methods: {
    loadContainer() {
      this.$store.dispatch('containers/get', { entity: this.$route.params.entity, collection: this.$route.params.collection, container: this.$route.params.container })
        .then((container: Container) => {
          this.localState.container = container;
        })
        .catch(err => this.$store.commit('snackbar/showError', err))
    }
  }
});
</script>